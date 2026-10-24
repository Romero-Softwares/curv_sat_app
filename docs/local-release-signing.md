# Assinatura local de releases

O CurvSat possui uma assinatura criptográfica própria para a cadeia de
atualizações. Ela é independente de certificadoras e impede que um manifesto
ou instalador alterado seja aceito pelo aplicativo.

## Registro técnico

- Formato: `merotec.release-manifest.v1`;
- Algoritmo: Ed25519;
- Chave pública do produto: `_Dz1GwGNduxGWtbQA2C69JrFdPpaevLZ0mR2J9J8-7M`;
- Identificador da chave: `ed25519:e587daae6f8fd5e563622814`;
- Dados protegidos: todos os campos do manifesto, inclusive versão, URL,
  notas, nome do instalador, tamanho e SHA-256;
- Chave privada: `licensing/release_signing_private_key.json` — local e fora
  do Git.

O formato canônico é JSON UTF-8 com chaves ordenadas, sem espaços e sem o campo
`local_signature`. A assinatura é codificada em Base64 URL-safe. Isso permite
validar a origem em qualquer ambiente que implemente Ed25519, sem depender de
um serviço online.

## Operação

O comando de publicação já assina o manifesto automaticamente depois de gerar
o executável. Para validar manualmente o par baixado:

```powershell
.venv\Scripts\python.exe -m curvsat.tools.release_signing verify `
  --manifest update_manifest.json `
  --artifact dist\ASCC-System-X.Y.Z.exe
```

O comando falha se a assinatura não for da chave pública registrada, se algum
metadado for alterado ou se o SHA-256/tamanho/nome do executável divergir.

## Proteção e rotação de chave

Guarde uma cópia cifrada da chave privada em local controlado e limite o acesso
somente a quem publica versões. Nunca envie esse arquivo por e-mail, Git,
mensageiro ou junto ao instalador. Se houver suspeita de exposição, gere uma
nova chave, atualize a chave pública no aplicativo, publique uma versão
transitória assinada pela chave antiga que anuncie a nova, e só então passe a
aceitar exclusivamente a nova chave.

## Limite perante o Windows

Esta é uma assinatura de integridade do produto; não é Authenticode. O Windows
e o SmartScreen exigem uma cadeia para uma autoridade confiável para tratar um
publicador como confiável. Para distribuição pública sem custo, a alternativa
compatível é MSIX pela Microsoft Store; certificados autoassinados servem para
desenvolvimento ou dispositivos corporativos administrados.

Referências: [opções de assinatura do Windows](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options),
[reputação do SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
e [Ed25519 no pacote cryptography](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/).
