import { render, screen } from "@testing-library/react";
import { StatusBadge } from "../components/StatusBadge";

test("renders status", () => {
  render(<StatusBadge status="completed" />);
  expect(screen.getByText("completed")).toBeInTheDocument();
});