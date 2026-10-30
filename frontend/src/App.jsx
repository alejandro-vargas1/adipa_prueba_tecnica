import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function App() {
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [resultado, setResultado] = useState(null);

  async function procesar() {
    setCargando(true);
    setError("");
    setResultado(null);
    const form = new FormData();
    form.append("file", archivo);
    try {
      const r = await fetch(`${API_URL}/extract`, { method: "POST", body: form });
      const data = await r.json().catch(() => ({}));
      if (r.ok) setResultado(data);
      else setError(data.detail ?? `Error ${r.status}`);
    } catch {
      setError("No se pudo conectar con el servidor");
    }
    setCargando(false);
  }

  function descargar() {
    const blob = new Blob([JSON.stringify(resultado, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "resultado.json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <main>
      <h1>Extractor de cuestionarios</h1>
      <p className="sub">
        Sube un PDF, DOCX o XLSX con un cuestionario y obtén sus ítems en JSON.
        <br />
        Verás cada ítem con su tipo, sus alternativas y la respuesta correcta si el documento la indica, y podrás
        descargar el resultado como archivo JSON.
      </p>
      <div className="acciones">
        <label className="archivo">
          <input type="file" accept=".pdf,.docx,.xlsx" onChange={(e) => setArchivo(e.target.files[0] ?? null)} />
          {archivo ? archivo.name : "Elegir archivo…"}
        </label>
        <button onClick={procesar} disabled={!archivo || cargando}>
          {cargando ? "Procesando…" : "Procesar"}
        </button>
      </div>

      {cargando && (
        <p className="aviso">
          <span className="spinner" />
          La primera petición puede tardar hasta un minuto si el servidor estaba dormido.
        </p>
      )}
      {error && <p className="error">{error}</p>}
      {resultado && (
        <section>
          <div className="resumen">
            <h2>
              {resultado.titulo}
              <span className="etiqueta">{resultado.idioma}</span>
              <span className="etiqueta">{resultado.total_items} ítems</span>
            </h2>
            <button className="secundario" onClick={descargar}>Descargar JSON</button>
          </div>
          <pre>{JSON.stringify(resultado, null, 2)}</pre>
        </section>
      )}
    </main>
  );
}
