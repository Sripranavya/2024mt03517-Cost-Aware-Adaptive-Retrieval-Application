// A small labelled query set for the in-app benchmark demo. Mirrors the backend
// bundled evaluation set (public-domain factual questions).
export const EVAL_SAMPLE: { query: string; reference: string }[] = [
  { query: "What is the capital of France?", reference: "The capital of France is Paris." },
  { query: "What is the capital of Japan?", reference: "The capital of Japan is Tokyo." },
  {
    query: "What is the highest mountain on Earth?",
    reference: "Mount Everest is the highest mountain above sea level on Earth.",
  },
  {
    query: "What does photosynthesis produce?",
    reference: "Photosynthesis produces glucose and releases oxygen.",
  },
  {
    query: "Who created the Python programming language?",
    reference: "Python was created by Guido van Rossum.",
  },
  {
    query: "What is the chemical formula of water?",
    reference: "Water has the chemical formula H2O.",
  },
  {
    query: "What is a Transformer in machine learning?",
    reference: "The Transformer is a neural network architecture based on attention mechanisms.",
  },
  {
    query: "What charge does an electron carry?",
    reference: "An electron carries a negative electric charge.",
  },
];
