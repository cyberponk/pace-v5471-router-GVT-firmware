// Pre-analysis: label + create functions from "name hexaddr" lines (recovered __ksymtab).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;

public class ImportSyms extends GhidraScript {
    @Override
    public void run() throws Exception {
        int n = 0;
        for (String l : Files.readAllLines(Paths.get(getScriptArgs()[0]))) {
            String[] p = l.trim().split("\\s+");
            if (p.length != 2) continue;
            var a = toAddr(Long.parseLong(p[1], 16));
            createLabel(a, p[0], true, SourceType.IMPORTED);
            n++;
        }
        println("imported " + n + " symbols");
    }
}
