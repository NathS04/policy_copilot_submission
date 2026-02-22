# Appendix B: External Materials

## B.1 Third-Party Libraries

The following open-source Python libraries were used in the development of Policy Copilot.

| Library | Version | License | Usage |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | PSF | Runtime environment |
| **OpenAI** | 1.x | Apache 2.0 | LLM API client |
| **Anthropic** | 0.x | MIT | LLM API client (alternate) |
| **Sentence-Transformers** | 2.x | Apache 2.0 | Bi-encoder embeddings |
| **FAISS-CPU** | 1.7.x | MIT | Vector indexing & search |
| **Pydantic** | 2.x | MIT | Config & data validation |
| **PyPDF** | 3.x | BSD-3 | PDF text extraction |
| **TikToken** | 0.x | MIT | Token counting |
| **Pytest** | 7.x | MIT | Unit testing framework |
| **Matplotlib** | 3.x | PSF | Figure generation |
| **Seaborn** | 0.x | BSD-3 | Statistical data visualization |
| **Streamlit** | 1.x | Apache 2.0 | Web interface framework |

## B.2 Licensing

The Policy Copilot source code is released under the **MIT License**. This permissive license allows for reuse, modification, and distribution, aligning with the project's goal of demonstrating reproducible research.

## B.3 External Datasets

No external datasets were used in this project. All data used for training, testing, and evaluation was synthetically generated to ensure privacy compliance and reproducibility.

-   **Policy Corpus**: Generated using GPT-4o with strict prompting to simulate typical internal organisational documents (Handbook, Security Addendum, HR Manual).
-   **Golden Set**: 63 queries manually crafted and auto-labelled based on the synthetic corpus.

## B.4 Development Tools

-   **VS Code**: Integrated Development Environment.
-   **Git**: Version control system.
-   **Poetry/Pip**: Dependency management.
-   **Black/Ruff**: Code formatting and linting.
