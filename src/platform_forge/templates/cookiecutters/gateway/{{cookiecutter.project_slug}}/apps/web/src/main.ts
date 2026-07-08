const app = document.querySelector<HTMLDivElement>("#app");

if (app) {
  app.innerHTML = `
    <main>
      <h1>{{ cookiecutter.project_name }}</h1>
      <p>Gateway URL: ${import.meta.env.VITE_GATEWAY_URL ?? "http://localhost:8000"}</p>
    </main>
  `;
}
