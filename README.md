# Neodent Studio — API de geração de materiais

Backend que gera os materiais personalizados (digitais em PNG, impressos
em PDF/CMYK), empacota em ZIP e envia por e-mail. Geração assíncrona via
jobs.

## Stack
Python 3.11 · Flask · Pillow · PyMuPDF · Ghostscript (CMYK) · Docker.

## Rodar
```bash
cp .env.example .env   # preencha o SMTP
docker compose up --build
```
A API sobe em `http://localhost:3006`.

## Endpoints
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/jobs` | Cria um job de geração. Body JSON; responde `{ jobId }`. |
| `GET`  | `/jobs/<id>` | Status: `pendente` · `processando` · `concluido` · `erro`. |
| `GET`  | `/download/<id>` | Baixa o ZIP gerado. |
| `GET`  | `/health` | Verificação de saúde. |

### `POST /jobs` — body
```json
{
  "tipo": "digital",
  "logo": "data:image/png;base64,...",
  "nome": "",
  "telefone": "",
  "cor": "roxo",
  "materiais": ["post-1", "post-2"],
  "email": "dentista@exemplo.com"
}
```
Use `logo` **ou** `nome`+`telefone`. `tipo` é `digital` ou `impresso`.

## Assets
- `app/assets/templates/digital/` — PNGs dos templates digitais.
- `app/assets/templates/print/` — PDFs dos templates de impressão.
- `app/assets/layout.json` — posição dos slots (espelha o
  `materialTemplates.ts` do frontend).
- `app/assets/fonts/` — fontes para os textos.

Os assets são montados como volume — trocar um template não exige
rebuild da imagem, basta substituir o arquivo na pasta.

## Notas
- O envio de e-mail é *best-effort*: se falhar, o job ainda conclui e o
  download fica disponível.
- O estado dos jobs é mantido em memória (protótipo).
