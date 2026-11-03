# Empório da Música — AI Customer Service Agent



A Python-based customer service agent developed as part of the **Artefact AI Engineer Technical Challenge**.



The application assists customers of a fictional musical instrument store by answering questions about products, promotions, orders, and store policies through a conversational interface powered by Google's Gemini API.



## Features



\- **Conversational AI:** Uses the Gemini API to understand customer requests and generate responses.

\- **Function calling:** Connects the language model to application tools for product catalog searches, promotions, and order-related operations.

\- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from the store's policy manual in PDF format.

\- **Policy retrieval:** Uses text extraction, sentence-aware chunking, token normalization, and BM25-based ranking.

\- **Order assistance:** Provides order-related functionality with customer data and privacy checks.

\- **Interactive CLI:** Supports customer conversations, conversation reset, and graceful session termination.

\- **Error handling:** Includes API configuration checks and retry handling for temporary service failures.



## Tech Stack



\- Python 3.11

\- Google GenAI SDK

\- Gemini 3.6 Flash

\- Pandas

\- NumPy

\- pypdf

\- python-dotenv

\- pytest



## Project Structure



```text

emporio-agent/

├── data/

│   ├── categories.csv

│   ├── customers.csv

│   ├── order\_items.csv

│   ├── orders.csv

│   ├── politicas\_da\_loja.pdf

│   ├── products.csv

│   └── promotions.csv

├── src/

│   └── emporio/

│       ├── \_\_init\_\_.py

│       ├── agent.py

│       ├── cli.py

│       ├── data.py

│       ├── llm.py

│       ├── orders.py

│       ├── policies.py

│       └── tools.py

├── tests/

│   ├── test\_data.py

│   ├── test\_orders.py

│   ├── test\_policies.py

│   └── test\_tools.py

├── conversations/

├── .env.example

├── .gitignore

├── pytest.ini

├── requirements.txt

└── README.md

```



## Getting Started



### 1. Requirements



\- Python 3.11

\- A Google Gemini API key



### 2. Create and activate a virtual environment



**Windows PowerShell:**



```powershell

python -m venv .venv

.venv\\Scripts\\Activate.ps1

```



**Linux/macOS:**



```bash

python -m venv .venv

source .venv/bin/activate

```



### 3. Install dependencies



```bash

pip install -r requirements.txt

```



### 4. Configure environment variables



Create your local environment file:



**Windows PowerShell:**



```powershell

Copy-Item .env.example .env

```



**Linux/macOS:**



```bash

cp .env.example .env

```



Set your Gemini API key in `.env`:



```env

GEMINI\_API\_KEY=your-gemini-api-key

GEMINI\_MODEL=gemini-3.6-flash

```



**Important:** Never commit your `.env` file or expose your API key. The `.env` file is excluded through `.gitignore`.



### 5. Run the application



From the project root:



**Windows PowerShell:**



```powershell

$env:PYTHONPATH = "src"

python -m emporio.cli

```



**Linux/macOS:**



```bash

PYTHONPATH=src python -m emporio.cli

```



The interactive interface accepts customer messages.



Available commands:



\- `limpar` — reset the current conversation.

\- `sair` — end the session.



## Architecture and Technical Decisions



### Conversational Agent and Function Calling



The agent uses the Gemini API to interpret customer requests and interact with application-defined tools.



This approach separates language understanding from business logic, allowing the model to access structured application functionality instead of relying exclusively on generated text.



### Retrieval-Augmented Generation (RAG)



The policy retrieval component uses the store's PDF policy manual as its knowledge source.



The retrieval pipeline includes:



1\. PDF text extraction using pypdf.

2\. Sentence-aware text chunking.

3\. Text and token normalization.

4\. BM25-based relevance scoring.

5\. Query coverage filtering to reduce unrelated matches.

6\. Retrieval of relevant passages with their source page information.



When no sufficiently relevant context is found, the retrieval component returns a `no\_relevant\_context` status.



### Data Handling



The application uses CSV files to represent the store's catalog, customers, orders, order items, categories, and promotions.



Pandas and NumPy support structured data processing.



### Error Handling



The Gemini integration includes configuration validation and retry handling for selected temporary API errors, with bounded retry attempts.



## Tests



The project includes automated tests covering:



\- Data loading and validation.

\- Order-related operations.

\- Policy document retrieval.

\- Application tools and their behavior.



Run the test suite from the project root:



```bash

pytest -v

```



**Latest recorded result:** 35 tests passed.



Automated tests do not replace a live API integration check. The Gemini connection and interactive CLI were also tested separately during development.



## Assumptions and Limitations



\- The store and its business data are fictional and intended for the technical challenge.

\- Responses about store policies depend on the information available in the supplied policy manual.

\- Retrieval uses lexical ranking (BM25) and token coverage filtering; it is not a semantic embedding-based search system.

\- Gemini API availability and response times depend on the external service.

\- The application is a technical challenge prototype, not a production-ready customer service deployment.



## Use of AI Coding Assistants



AI coding assistants were used as development support during implementation, debugging, code review, and documentation.



Claude was used for implementation assistance. ChatGPT was used for technical troubleshooting, reviewing implementation decisions, validating behavior, and documentation support.



The final implementation and submitted work were reviewed and tested by the developer.



## Example Conversations



The `conversations/` directory is reserved for example interaction records.



## Challenge



**Artefact — AI Engineer Technical Challenge**
