import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import keycloak from "./keycloak";

keycloak
  .init({
    onLoad: "login-required",
    pkceMethod: "S256",
    checkLoginIframe: false,
  })
  .then((authenticated) => {
    if (!authenticated) {
      keycloak.login();
    }

    setInterval(() => {
      keycloak.updateToken(30).catch(() => keycloak.login());
    }, 10000);

    ReactDOM.createRoot(
      document.getElementById("root")!
    ).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  })
  .catch(console.error);
