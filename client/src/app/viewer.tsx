import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@fontsource/newsreader/400.css";
import "@fontsource/newsreader/500.css";

import { ViewerPage } from "@/pages/viewer";

import "./global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ViewerPage />
  </StrictMode>,
);
