// Decompile functions named in the script arguments (or at 0x addresses), print C to stdout.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;

public class Decomp extends GhidraScript {
    @Override
    public void run() throws Exception {
        DecompInterface d = new DecompInterface();
        d.openProgram(currentProgram);
        for (String a : getScriptArgs()) {
            Function f = null;
            if (a.startsWith("0x")) {
                f = getFunctionContaining(toAddr(a));
            } else {
                for (Function g : currentProgram.getFunctionManager().getFunctions(true)) {
                    if (g.getName().equals(a)) { f = g; break; }
                }
            }
            if (f == null) { println("=== " + a + ": not found"); continue; }
            DecompileResults r = d.decompileFunction(f, 120, monitor);
            println("=== " + a + " @ " + f.getEntryPoint());
            println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "decompile failed: " + r.getErrorMessage());
        }
    }
}
