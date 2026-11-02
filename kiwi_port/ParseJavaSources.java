import com.sun.source.util.JavacTask;
import java.util.List;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.ToolProvider;

/** Parse without resolving Android/Chromium dependencies; compilation is still mandatory. */
class ParseJavaSources {
    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("A JDK is required");
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (var files = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavacTask task = (JavacTask) compiler.getTask(null, files, diagnostics,
                    List.of("-proc:none"), null, files.getJavaFileObjects(args));
            task.parse();
            boolean failed = false;
            for (var diagnostic : diagnostics.getDiagnostics()) {
                if (diagnostic.getKind() == Diagnostic.Kind.ERROR) {
                    System.err.println(diagnostic);
                    failed = true;
                }
            }
            if (failed) System.exit(1);
        }
        System.out.println("Parsed " + args.length + " Java sources; no syntax errors");
    }
}
