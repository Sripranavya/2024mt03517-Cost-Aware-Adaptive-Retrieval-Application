"""Bundled public-domain sample corpus and evaluation query set.

This small corpus lets the system run end-to-end with zero setup (no AWS, no
network): the engine seeds the local vector store from it on first use. The
``scripts/seed_corpus.py`` script can expand it with live Wikipedia/arXiv content.
All content here is short, factual, and public-domain in nature.

Each document is tagged with the ``source`` it represents (``local_corpus``,
``wikipedia``, or ``arxiv``) so the source connectors can filter the shared index.
"""

from __future__ import annotations

SAMPLE_DOCUMENTS: list[dict[str, str]] = [
    {
        "id": "local:paris",
        "source": "local_corpus",
        "title": "France",
        "text": (
            "France is a country in Western Europe. The capital of France is Paris, "
            "which sits on the River Seine and is the country's most populous city."
        ),
    },
    {
        "id": "local:japan",
        "source": "local_corpus",
        "title": "Japan",
        "text": (
            "Japan is an island country in East Asia. The capital of Japan is Tokyo. "
            "Japan has a population of approximately 125 million people."
        ),
    },
    {
        "id": "local:everest",
        "source": "local_corpus",
        "title": "Mount Everest",
        "text": (
            "Mount Everest is the highest mountain above sea level on Earth, with a "
            "peak at 8,849 metres. It lies in the Himalayas on the border between "
            "Nepal and the Tibet Autonomous Region of China."
        ),
    },
    {
        "id": "wiki:photosynthesis",
        "source": "wikipedia",
        "title": "Photosynthesis",
        "text": (
            "Photosynthesis is the process by which green plants, algae, and some "
            "bacteria convert light energy into chemical energy. It uses carbon "
            "dioxide and water to produce glucose and releases oxygen as a byproduct."
        ),
    },
    {
        "id": "wiki:gravity",
        "source": "wikipedia",
        "title": "Gravity",
        "text": (
            "Gravity is a fundamental force by which all objects with mass are "
            "attracted to one another. On Earth, gravity gives weight to physical "
            "objects and causes them to fall toward the ground when dropped."
        ),
    },
    {
        "id": "wiki:python",
        "source": "wikipedia",
        "title": "Python (programming language)",
        "text": (
            "Python is a high-level, general-purpose programming language created by "
            "Guido van Rossum and first released in 1991. It emphasises code "
            "readability and supports multiple programming paradigms."
        ),
    },
    {
        "id": "wiki:water",
        "source": "wikipedia",
        "title": "Water",
        "text": (
            "Water is a chemical compound with the formula H2O. Each molecule "
            "contains one oxygen atom and two hydrogen atoms connected by covalent "
            "bonds. Water covers about 71 percent of Earth's surface."
        ),
    },
    {
        "id": "wiki:electron",
        "source": "wikipedia",
        "title": "Electron",
        "text": (
            "An electron is a subatomic particle with a negative electric charge. "
            "Electrons participate in chemical bonding and the flow of electric "
            "current. The electron is a fundamental particle of the lepton family."
        ),
    },
    {
        "id": "arxiv:transformer",
        "source": "arxiv",
        "title": "Attention Is All You Need",
        "text": (
            "The Transformer is a neural network architecture based solely on "
            "attention mechanisms, dispensing with recurrence and convolutions. "
            "Self-attention relates different positions of a sequence to compute a "
            "representation of that sequence."
        ),
    },
    {
        "id": "arxiv:pomdp",
        "source": "arxiv",
        "title": "Partially Observable Markov Decision Processes",
        "text": (
            "A partially observable Markov decision process (POMDP) models an agent "
            "that cannot directly observe the underlying state. The agent maintains "
            "a belief, a probability distribution over states, and updates it using "
            "Bayes' rule after each action and observation."
        ),
    },
    {
        "id": "arxiv:rag",
        "source": "arxiv",
        "title": "Retrieval-Augmented Generation",
        "text": (
            "Retrieval-augmented generation (RAG) combines a parametric language "
            "model with a non-parametric retrieval component. Relevant documents are "
            "retrieved from a corpus and conditioned on to improve the factual "
            "accuracy of generated answers."
        ),
    },
    {
        "id": "arxiv:reinforcement",
        "source": "arxiv",
        "title": "Reinforcement Learning",
        "text": (
            "Reinforcement learning is a paradigm in which an agent learns to make "
            "decisions by interacting with an environment and receiving rewards. The "
            "goal is to learn a policy that maximises expected cumulative reward."
        ),
    },
]


EVAL_QUERIES: list[dict[str, str]] = [
    {
        "query": "What is the capital of France?",
        "reference": "The capital of France is Paris.",
    },
    {
        "query": "What is the capital of Japan?",
        "reference": "The capital of Japan is Tokyo.",
    },
    {
        "query": "What is the highest mountain on Earth?",
        "reference": "Mount Everest is the highest mountain above sea level on Earth.",
    },
    {
        "query": "What does photosynthesis produce?",
        "reference": "Photosynthesis produces glucose and releases oxygen.",
    },
    {
        "query": "Who created the Python programming language?",
        "reference": "Python was created by Guido van Rossum.",
    },
    {
        "query": "What is the chemical formula of water?",
        "reference": "Water has the chemical formula H2O.",
    },
    {
        "query": "What is a Transformer in machine learning?",
        "reference": (
            "The Transformer is a neural network architecture based on "
            "attention mechanisms."
        ),
    },
    {
        "query": "How does a POMDP agent handle unobservable state?",
        "reference": (
            "A POMDP agent maintains a belief over states and updates it with "
            "Bayes' rule."
        ),
    },
    {
        "query": "What charge does an electron carry?",
        "reference": "An electron carries a negative electric charge.",
    },
    {
        "query": "What is retrieval-augmented generation?",
        "reference": (
            "RAG combines a language model with retrieval of relevant documents "
            "to improve factual accuracy."
        ),
    },
]
