import type { Metadata } from "next";
import React from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meetingbot Write Message",
  description: "Upload an image and send it to the tango endpoint.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
          <header className="mb-10">
            <h1 className="text-3xl font-semibold text-gray-900">Write message</h1>
            <p className="mt-2 text-sm text-gray-600">
              Carga una imagen, revisa la previsualización y envíala al endpoint /tango.
            </p>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
