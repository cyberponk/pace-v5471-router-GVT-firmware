/* Emit struct offsets of the candidate kernel headers as data (compile with -S, never linked). */
#include <linux/kernel.h>
#include <linux/stddef.h>
#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <linux/usb.h>

#define O(s, f) const int o__##s##__##f = offsetof(struct s, f);
#define Z(s) const int z__##s = sizeof(struct s);
#define OR(s, f) const int o__##s##__##f = offsetof(struct s, f);

O(sk_buff, next) O(sk_buff, dev) O(sk_buff, destructor) O(sk_buff, blog_p) O(sk_buff, data) O(sk_buff, len)
O(sk_buff, recycle_hook) O(sk_buff, tail) O(sk_buff, end) O(sk_buff, head) O(sk_buff, users) O(sk_buff, nfct)
O(sk_buff, nfct_reasm) O(sk_buff, tc_word) O(sk_buff, transport_header) O(sk_buff, network_header)
O(sk_buff, mac_header) O(sk_buff, iif) O(sk_buff, sk) O(sk_buff, tstamp) O(sk_buff, dst) O(sk_buff, sp)
O(sk_buff, cb) O(sk_buff, data_len) O(sk_buff, mac_len) O(sk_buff, hdr_len) O(sk_buff, protocol)
O(sk_buff, nf_bridge) O(sk_buff, vlan_count) O(sk_buff, vlan_tpid) O(sk_buff, vlan_header) O(sk_buff, rxdev)
O(sk_buff, truesize) Z(sk_buff)
O(skb_shared_info, dirty_p) O(skb_shared_info, gso_size) O(skb_shared_info, gso_segs) O(skb_shared_info, gso_type)
Z(skb_shared_info)
O(net_device, name) O(net_device, state) O(net_device, napi_list) O(net_device, stats) O(net_device, netdev_ops)
O(net_device, header_ops) O(net_device, flags) O(net_device, padded) O(net_device, mtu) O(net_device, type)
O(net_device, hard_header_len) O(net_device, addr_len) O(net_device, dev_addr) O(net_device, broadcast)
O(net_device, _tx) O(net_device, num_tx_queues) O(net_device, real_num_tx_queues) O(net_device, tx_queue_len)
O(net_device, reg_state) O(net_device, set_mac_address) O(net_device, validate_addr) O(net_device, change_mtu)
Z(net_device)
O(net_device_ops, ndo_change_mtu) O(net_device_ops, ndo_get_stats)
Z(urb) Z(usb_device) Z(usb_interface)
O(urb, dev) O(urb, pipe) O(urb, status) O(urb, transfer_flags) O(urb, transfer_buffer) O(urb, transfer_buffer_length)
O(urb, actual_length) O(urb, context) O(urb, complete)
/* extra net_device fields, printed as info to locate config differences */
O(net_device, rx_queue) O(net_device, tx_global_lock) O(net_device, trans_start) O(net_device, watchdog_timeo)
O(net_device, watchdog_timer) O(net_device, refcnt) O(net_device, todo_list) O(net_device, link_watch_next)
O(net_device, destructor) O(net_device, ml_priv) O(net_device, br_port) O(net_device, dev)
O(net_device, sysfs_groups) O(net_device, rtnl_link_ops) O(net_device, gso_max_size) O(net_device, open)
O(urb, urb_list) O(urb, anchor_list) O(urb, anchor) O(usb_device, dev) O(usb_device, actconfig) O(usb_host_config, interface)
O(usb_interface, condition) O(usb_interface, dev) O(usb_driver, drvwrap) O(device, driver) O(device, driver_data)
#include <linux/module.h>
O(module, init) O(module, exit) Z(module)
