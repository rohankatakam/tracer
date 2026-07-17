import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

test('renders the public demo fixture list', async () => {
  render(<App />);

  expect(await screen.findByRole('heading', { name: /public demo bugs/i })).toBeInTheDocument();
  expect(screen.getByText(/website freezes when changing currency/i)).toBeInTheDocument();
  expect(screen.getByText(/static examples for illustrating tracer's review flow/i)).toBeInTheDocument();
});
