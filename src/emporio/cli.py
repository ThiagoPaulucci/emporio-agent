
"""Interactive command-line interface for Empório da Música."""

from __future__ import annotations

from dotenv import load_dotenv

from .agent import EmporioAgent
from .llm import LLMConfigurationError, LLMRequestError


def main() -> None:
    """Start an interactive customer service session."""
    load_dotenv()

    print("\n" + "=" * 58)
    print("             EMPÓRIO DA MÚSICA")
    print("          Atendimento ao Cliente")
    print("=" * 58)
    print("Olá! Sou o assistente virtual do Empório da Música.")
    print("Como posso ajudar você hoje?")
    print("\nDigite 'sair' para encerrar ou 'limpar' para reiniciar a conversa.")
    print("-" * 58)

    agent = EmporioAgent()

    while True:
        try:
            message = input("\nVocê: ").strip()

            if not message:
                continue

            command = message.casefold()

            if command in {"sair", "exit", "quit"}:
                print("\nAssistente: Obrigado pelo contato!")
                print("Até logo e boas compras!")
                break

            if command in {"limpar", "reset", "reiniciar"}:
                agent.reset()
                print("\nAssistente: Nossa conversa foi reiniciada. Como posso ajudar?")
                continue

            response = agent.chat(message)
            print(f"\nAssistente: {response}")

        except (EOFError, KeyboardInterrupt):
            print("\n\nAssistente: Atendimento encerrado. Até logo!")
            break

        except LLMConfigurationError as error:
            print(f"\nErro de configuração: {error}")
            print(
                "Verifique se a variável GEMINI_API_KEY está definida "
                "no arquivo .env."
            )
            break

        except LLMRequestError:
            print(
                "\nAssistente: Estou com dificuldade para acessar o serviço "
                "de atendimento. Tente novamente em instantes."
            )

        except Exception:
            print(
                "\nAssistente: Ocorreu um erro inesperado. "
                "Tente novamente."
            )


if __name__ == "__main__":
    main()
