import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import WriteMessageForm from "./WriteMessageForm";

describe("WriteMessageForm", () => {
  it("renders the file input and submit button", () => {
    render(<WriteMessageForm />);

    expect(screen.getByLabelText(/imagen/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /write message/i })).toBeInTheDocument();
  });

  it("blocks files that are not images", async () => {
    render(<WriteMessageForm />);

    const fileInput = screen.getByLabelText(/imagen/i) as HTMLInputElement;
    const badFile = new File(["text"], "notes.txt", { type: "text/plain" });

    fireEvent.change(fileInput, { target: { files: [badFile] } });

    await waitFor(() => {
      expect(screen.getByText(/archivo de imagen válido/i)).toBeInTheDocument();
    });
  });
});
