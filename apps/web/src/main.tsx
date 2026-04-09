import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "@/app/app";
import "@/styles/globals.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";

ReactDOM.createRoot(document.getElementById("app")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
