def render_head_html():
    return """
    <html><head><title>Descarga en Progreso</title>
    <link rel="stylesheet" href="/static/estilos.css">
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            document.documentElement.classList.add('dark');
        });
        function toggleMode() {
            document.documentElement.classList.toggle('dark');
        }
    </script>
    </head><body>
    <div class="navbar">
        <button class='toggle-btn' onclick='toggleMode()'>🌓 Modo claro/oscuro</button>
    </div>
    <div class="contenedor">
    <h2>📦 Fase 1: escaneando archivos en Drive...</h2>
    """

def render_html_close():
    return """
        </div>
        </body></html>
    """
