"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useMemo, useState } from "react";

const MAX_FILE_SIZE_BYTES = 6 * 1024 * 1024; // 6MB safety limit

function formatBytes(bytes: number): string {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, exponent);
  return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

export default function WriteMessageForm() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [base64Image, setBase64Image] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [conversationId, setConversationId] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [fileTooLarge, setFileTooLarge] = useState<boolean>(false);

  const helperText = useMemo(
    () =>
      fileTooLarge
        ? `El archivo es demasiado grande. Máximo ${formatBytes(MAX_FILE_SIZE_BYTES)}.`
        : "Formatos compatibles: PNG, JPG, GIF o WEBP.",
    [fileTooLarge]
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setError("");
    setStatus("idle");
    setStatusMessage("");
    setFileTooLarge(false);

    if (!file) {
      setImagePreview(null);
      setBase64Image(null);
      setFileName("");
      setMimeType("");
      return;
    }

    if (!file.type.startsWith("image/")) {
      setError("Selecciona un archivo de imagen válido.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setFileTooLarge(true);
      setError(`El archivo supera el límite de ${formatBytes(MAX_FILE_SIZE_BYTES)}.`);
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const [, base64String] = result.split(",");
      setImagePreview(result);
      setBase64Image(base64String);
      setMimeType(file.type);
      setFileName(file.name);
    };
    reader.onerror = () => {
      setError("Hubo un problema al leer el archivo. Inténtalo de nuevo.");
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!base64Image || !mimeType) {
      setError("Selecciona una imagen antes de enviar.");
      return;
    }

    setStatus("loading");
    setError("");
    setStatusMessage("Enviando imagen al endpoint /tango...");

    try {
      const response = await fetch("/tango", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image: base64Image,
          mime_type: mimeType,
          user_id: userId || null,
          conversation_id: conversationId || null,
        }),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(errorBody || "El servidor respondió con un error.");
      }

      setStatus("success");
      setStatusMessage("Imagen enviada correctamente a /tango.");
    } catch (err) {
      const reason = err instanceof Error ? err.message : "Error desconocido.";
      setStatus("error");
      setStatusMessage("");
      setError(reason);
    }
  };

  const showReset = !!imagePreview || !!userId || !!conversationId;

  const resetForm = () => {
    setImagePreview(null);
    setBase64Image(null);
    setMimeType("");
    setFileName("");
    setUserId("");
    setConversationId("");
    setStatus("idle");
    setStatusMessage("");
    setError("");
    setFileTooLarge(false);
  };

  return (
    <section className="space-y-6 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-200">
      <div className="space-y-2">
        <p className="text-base font-medium text-gray-900">Adjunta una imagen para escribir un mensaje</p>
        <p className="text-sm text-gray-600">
          Se convertirá a base64 con FileReader y se enviará como JSON al endpoint <code className="rounded bg-gray-100 px-1 py-0.5">/tango</code>.
        </p>
      </div>

      <form className="space-y-6" onSubmit={handleSubmit}>
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-900" htmlFor="image">
            Imagen
          </label>
          <div className="flex flex-col gap-3 rounded-xl border border-dashed border-gray-300 bg-gray-50 p-4 transition hover:border-blue-400">
            <input
              id="image"
              name="image"
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full cursor-pointer text-sm text-gray-700 file:mr-4 file:rounded-full file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-blue-700"
            />
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>{helperText}</span>
              {fileName ? <span className="font-medium text-gray-800">{fileName}</span> : null}
            </div>
            {fileTooLarge ? (
              <p className="text-sm font-medium text-red-600" role="alert">
                El archivo supera el tamaño permitido.
              </p>
            ) : null}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1 text-sm font-medium text-gray-900" htmlFor="userId">
            Usuario (user_id)
            <input
              id="userId"
              name="userId"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="Opcional"
              autoComplete="off"
            />
          </label>

          <label className="space-y-1 text-sm font-medium text-gray-900" htmlFor="conversationId">
            Conversación (conversation_id)
            <input
              id="conversationId"
              name="conversationId"
              value={conversationId}
              onChange={(event) => setConversationId(event.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              placeholder="Opcional"
              autoComplete="off"
            />
          </label>
        </div>

        {imagePreview ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-900">Previsualización</p>
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-gray-100 shadow-inner">
              <img
                src={imagePreview}
                alt="Previsualización de la imagen seleccionada"
                className="max-h-80 w-full object-contain"
              />
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-600">Selecciona una imagen para ver la previsualización.</p>
        )}

        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
            {error}
          </div>
        ) : null}

        {status !== "idle" && !error ? (
          <div
            className={`rounded-lg border px-4 py-3 text-sm ${
              status === "success"
                ? "border-green-200 bg-green-50 text-green-800"
                : status === "loading"
                  ? "border-blue-200 bg-blue-50 text-blue-800"
                  : "border-red-200 bg-red-50 text-red-800"
            }`}
            role="status"
          >
            {status === "loading" && <span className="mr-2 inline-flex h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-transparent" />}
            {statusMessage || (status === "error" ? "Ocurrió un error al enviar." : null)}
          </div>
        ) : null}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-gray-500">
            El envío incluye <code className="rounded bg-gray-100 px-1 py-0.5">image</code>, <code className="rounded bg-gray-100 px-1 py-0.5">mime_type</code>,
            <code className="rounded bg-gray-100 px-1 py-0.5">user_id</code> y <code className="rounded bg-gray-100 px-1 py-0.5">conversation_id</code>.
          </p>
          <div className="flex gap-3">
            {showReset && (
              <button
                type="button"
                onClick={resetForm}
                className="inline-flex items-center justify-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              >
                Limpiar
              </button>
            )}
            <button
              type="submit"
              disabled={status === "loading" || !base64Image || fileTooLarge}
              className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-blue-300"
            >
              {status === "loading" ? "Enviando..." : "Write message"}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
