/*
 * dotproxy: DNS over UDP (local) -> DNS over TLS (RFC 7858) forwarder for the router.
 * dnsmasq forwards to it (server=127.0.0.1#5053); it keeps one TLS connection to the first
 * server that works, pipelines the queries over it (2-byte length framing, own query ids) and
 * sends each answer back to whoever asked. mbedTLS 3.6 (TLS 1.2/1.3), certificate chain and
 * server name verified.
 *
 *   dotproxy [-l port] [-c cafile] -s ip@name [-s ip@name ...]
 *
 * The router boots with its clock in 2009 until NTP has synced, and NTP needs DNS: while the clock
 * is before the build time, an expired / not yet valid certificate is accepted (the chain and the
 * name are still checked).
 */
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <syslog.h>
#include <time.h>
#include <unistd.h>

#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>
#include <mbedtls/net_sockets.h>
#include <mbedtls/ssl.h>
#include <mbedtls/x509_crt.h>
#include <psa/crypto.h>

#ifndef BUILD_EPOCH
#define BUILD_EPOCH 0
#endif

#define MAX_SERVERS 4
#define MAX_PENDING 128
#define QUERY_TTL 5        /* seconds a query waits for its answer */
#define IO_TIMEOUT 3       /* seconds: TCP connect, TLS handshake, blocking reads/writes */

struct server { struct sockaddr_in addr; char name[128]; };
struct pending {
	int used;
	time_t at;
	unsigned short cid, id;       /* client's query id, ours */
	struct sockaddr_in from;
	unsigned char *q; int qlen;   /* the query (our id), resent after a reconnect */
};

static struct server srv[MAX_SERVERS];
static int nsrv, cur;
static struct pending pend[MAX_PENDING];
static unsigned short next_id;

static mbedtls_entropy_context entropy;
static mbedtls_ctr_drbg_context drbg;
static mbedtls_x509_crt ca;
static mbedtls_ssl_config conf;
static mbedtls_ssl_context ssl;
static mbedtls_net_context net;
static int up;                   /* TLS session established */
static unsigned char rbuf[2 + 65535];
static int rlen;

static void logm(int pri, const char *fmt, const char *a, int b)
{
	syslog(pri, fmt, a, b);
}

static int verify_cb(void *u, mbedtls_x509_crt *crt, int depth, uint32_t *flags)
{
	(void)u; (void)crt; (void)depth;
	if (time(NULL) < (time_t)BUILD_EPOCH)
		*flags &= ~(MBEDTLS_X509_BADCERT_EXPIRED | MBEDTLS_X509_BADCERT_FUTURE |
			    MBEDTLS_X509_BADCRL_EXPIRED | MBEDTLS_X509_BADCRL_FUTURE);
	return 0;
}

static void tls_close(void)
{
	if (net.fd >= 0) {
		if (up)
			mbedtls_ssl_close_notify(&ssl);
		mbedtls_net_free(&net);
	}
	mbedtls_ssl_free(&ssl);
	mbedtls_net_init(&net);
	up = 0;
	rlen = 0;
}

static int tcp_connect(const struct sockaddr_in *a)
{
	int fd = socket(AF_INET, SOCK_STREAM, 0), fl, err = 0, one = 1;
	socklen_t el = sizeof(err);
	struct pollfd p;
	struct timeval tv = { IO_TIMEOUT, 0 };

	if (fd < 0)
		return -1;
	fl = fcntl(fd, F_GETFL);
	fcntl(fd, F_SETFL, fl | O_NONBLOCK);
	if (connect(fd, (const struct sockaddr *)a, sizeof(*a)) < 0 && errno != EINPROGRESS)
		goto fail;
	p.fd = fd; p.events = POLLOUT;
	if (poll(&p, 1, IO_TIMEOUT * 1000) != 1 || getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &el) < 0 || err)
		goto fail;
	fcntl(fd, F_SETFL, fl);
	setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
	setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
	setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
	return fd;
fail:
	close(fd);
	return -1;
}

/* connect to the current server, else the next ones; 0 = up */
static int tls_open(void)
{
	int i, r;

	for (i = 0; i < nsrv; i++) {
		struct server *s = &srv[cur];
		tls_close();
		mbedtls_ssl_init(&ssl);
		net.fd = tcp_connect(&s->addr);
		if (net.fd < 0) {
			logm(LOG_WARNING, "dotproxy: %s: connect failed (%d)", s->name, errno);
		} else if ((r = mbedtls_ssl_setup(&ssl, &conf)) == 0 && (r = mbedtls_ssl_set_hostname(&ssl, s->name)) == 0) {
			mbedtls_ssl_set_bio(&ssl, &net, mbedtls_net_send, mbedtls_net_recv, NULL);
			time_t end = time(NULL) + 2 * IO_TIMEOUT;
			/* a stalled server makes the reads time out (SO_RCVTIMEO): WANT_READ, give up after a while */
			while (((r = mbedtls_ssl_handshake(&ssl)) == MBEDTLS_ERR_SSL_WANT_READ || r == MBEDTLS_ERR_SSL_WANT_WRITE) &&
			       time(NULL) < end)
				;
			if (r == 0) {
				up = 1;
				return 0;
			}
			logm(LOG_WARNING, "dotproxy: %s: TLS handshake failed (-0x%04x)", s->name, -r);
			if (r == MBEDTLS_ERR_X509_CERT_VERIFY_FAILED)
				syslog(LOG_WARNING, "dotproxy: certificate flags 0x%x", (unsigned)mbedtls_ssl_get_verify_result(&ssl));
		}
		cur = (cur + 1) % nsrv;
	}
	tls_close();
	return -1;
}

static int tls_write_all(const unsigned char *b, int n)
{
	int r;
	time_t end = time(NULL) + 2 * IO_TIMEOUT;
	while (n > 0) {
		r = mbedtls_ssl_write(&ssl, b, n);
		if ((r == MBEDTLS_ERR_SSL_WANT_READ || r == MBEDTLS_ERR_SSL_WANT_WRITE) && time(NULL) < end)
			continue;
		if (r <= 0)
			return -1;
		b += r; n -= r;
	}
	return 0;
}

static int send_query(struct pending *p)
{
	unsigned char hdr[2] = { p->qlen >> 8, p->qlen & 0xff };
	if (!up)
		return -1;
	if (tls_write_all(hdr, 2) || tls_write_all(p->q, p->qlen)) {
		tls_close();
		return -1;
	}
	return 0;
}

/* (re)connect and send every query still waiting */
static void resend_all(void)
{
	int i, tries;
	for (tries = 0; tries < 2; tries++) {
		if (!up && tls_open())
			return;
		for (i = 0; i < MAX_PENDING; i++)
			if (pend[i].used && send_query(&pend[i]))
				break;
		if (i == MAX_PENDING)
			return;
		cur = (cur + 1) % nsrv;
	}
}

static void drop(struct pending *p)
{
	free(p->q);
	memset(p, 0, sizeof(*p));
}

static void expire(void)
{
	time_t now = time(NULL);
	int i;
	for (i = 0; i < MAX_PENDING; i++)
		if (pend[i].used && (now - pend[i].at > QUERY_TTL || now < pend[i].at))
			drop(&pend[i]);
}

static void got_query(int us)
{
	unsigned char b[4096];
	struct sockaddr_in from;
	socklen_t fl = sizeof(from);
	int n = recvfrom(us, b, sizeof(b), 0, (struct sockaddr *)&from, &fl), i, slot = -1;
	time_t oldest = 0;

	if (n < 12)
		return;
	expire();
	for (i = 0; i < MAX_PENDING; i++) {
		if (!pend[i].used) { slot = i; break; }
		if (slot < 0 || pend[i].at < oldest) { slot = i; oldest = pend[i].at; }
	}
	if (pend[slot].used)
		drop(&pend[slot]);
	struct pending *p = &pend[slot];
	p->q = malloc(n);
	if (!p->q)
		return;
	p->used = 1;
	p->at = time(NULL);
	p->from = from;
	p->cid = (b[0] << 8) | b[1];
	p->id = ++next_id;
	b[0] = p->id >> 8; b[1] = p->id & 0xff;
	memcpy(p->q, b, n);
	p->qlen = n;
	if (send_query(p))
		resend_all();
}

/* complete answers in rbuf -> clients */
static void deliver(int us)
{
	int i;
	while (rlen >= 2) {
		int n = (rbuf[0] << 8) | rbuf[1];
		if (rlen < 2 + n)
			return;
		if (n >= 12) {
			unsigned short id = (rbuf[2] << 8) | rbuf[3];
			for (i = 0; i < MAX_PENDING; i++)
				if (pend[i].used && pend[i].id == id) {
					rbuf[2] = pend[i].cid >> 8; rbuf[3] = pend[i].cid & 0xff;
					sendto(us, rbuf + 2, n, 0, (struct sockaddr *)&pend[i].from, sizeof(pend[i].from));
					drop(&pend[i]);
					break;
				}
		}
		memmove(rbuf, rbuf + 2 + n, rlen - 2 - n);
		rlen -= 2 + n;
	}
}

static void got_answer(int us)
{
	int r;
	do {
		r = mbedtls_ssl_read(&ssl, rbuf + rlen, sizeof(rbuf) - rlen);
		if (r == MBEDTLS_ERR_SSL_WANT_READ || r == MBEDTLS_ERR_SSL_WANT_WRITE)
			return;
#ifdef MBEDTLS_SSL_PROTO_TLS1_3
		if (r == MBEDTLS_ERR_SSL_RECEIVED_NEW_SESSION_TICKET)
			continue;
#endif
		if (r <= 0) {
			/* closed by the server (idle) or broken: queries still waiting go on a new connection */
			tls_close();
			for (r = 0; r < MAX_PENDING; r++)
				if (pend[r].used) {
					resend_all();
					break;
				}
			return;
		}
		rlen += r;
		deliver(us);
	} while (up && mbedtls_ssl_get_bytes_avail(&ssl) > 0);
}

static void usage(void)
{
	fprintf(stderr, "usage: dotproxy [-l port] [-c cafile] -s ip@tls-name [-s ...]\n");
	exit(2);
}

int main(int argc, char **argv)
{
	int port = 5053, o, us, one = 1;
	const char *cafile = "/etc/ssl/certs/ca-certificates.crt";
	struct sockaddr_in la;

	while ((o = getopt(argc, argv, "l:c:s:")) != -1) {
		char *at;
		switch (o) {
		case 'l': port = atoi(optarg); break;
		case 'c': cafile = optarg; break;
		case 's':
			at = strchr(optarg, '@');
			if (!at || nsrv == MAX_SERVERS || at - optarg > 15)
				usage();
			*at = 0;
			memset(&srv[nsrv], 0, sizeof(srv[nsrv]));
			srv[nsrv].addr.sin_family = AF_INET;
			srv[nsrv].addr.sin_port = htons(853);
			if (inet_pton(AF_INET, optarg, &srv[nsrv].addr.sin_addr) != 1)
				usage();
			snprintf(srv[nsrv].name, sizeof(srv[nsrv].name), "%s", at + 1);
			nsrv++;
			break;
		default: usage();
		}
	}
	if (!nsrv)
		usage();
	openlog("dotproxy", LOG_PID, LOG_DAEMON);
	signal(SIGPIPE, SIG_IGN);

	if (psa_crypto_init() != PSA_SUCCESS) {
		syslog(LOG_ERR, "dotproxy: psa_crypto_init failed");
		return 1;
	}
	mbedtls_entropy_init(&entropy);
	mbedtls_ctr_drbg_init(&drbg);
	mbedtls_x509_crt_init(&ca);
	mbedtls_ssl_config_init(&conf);
	mbedtls_net_init(&net);
	mbedtls_ssl_init(&ssl);
	if (mbedtls_ctr_drbg_seed(&drbg, mbedtls_entropy_func, &entropy, (const unsigned char *)"dotproxy", 8) ||
	    mbedtls_x509_crt_parse_file(&ca, cafile) < 0 ||
	    mbedtls_ssl_config_defaults(&conf, MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT)) {
		syslog(LOG_ERR, "dotproxy: TLS setup failed (CA file %s)", cafile);
		return 1;
	}
	mbedtls_ssl_conf_authmode(&conf, MBEDTLS_SSL_VERIFY_REQUIRED);
	mbedtls_ssl_conf_ca_chain(&conf, &ca, NULL);
	mbedtls_ssl_conf_rng(&conf, mbedtls_ctr_drbg_random, &drbg);
	mbedtls_ssl_conf_verify(&conf, verify_cb, NULL);
	mbedtls_ssl_conf_min_tls_version(&conf, MBEDTLS_SSL_VERSION_TLS1_2);

	us = socket(AF_INET, SOCK_DGRAM, 0);
	memset(&la, 0, sizeof(la));
	la.sin_family = AF_INET;
	la.sin_port = htons(port);
	la.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	setsockopt(us, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
	if (us < 0 || bind(us, (struct sockaddr *)&la, sizeof(la)) < 0) {
		syslog(LOG_ERR, "dotproxy: cannot listen on 127.0.0.1:%d", port);
		return 1;
	}
	syslog(LOG_INFO, "dotproxy: listening on 127.0.0.1:%d, %d servers", port, nsrv);
	next_id = (unsigned short)(time(NULL) ^ getpid());

	for (;;) {
		struct pollfd p[2] = { { us, POLLIN, 0 }, { up ? net.fd : -1, POLLIN, 0 } };
		int r = poll(p, 2, 1000);
		if (r < 0 && errno != EINTR)
			return 1;
		if (r > 0 && up && (p[1].revents & (POLLIN | POLLHUP | POLLERR)))
			got_answer(us);
		if (r > 0 && (p[0].revents & POLLIN))
			got_query(us);
		expire();
	}
}
