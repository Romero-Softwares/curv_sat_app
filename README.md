# Curva de Saturação Almen

Aplicação desktop para ajustar medições de lâminas Almen ao modelo exponencial e indicar os pontos de saturação T e 2T. A curva exige no mínimo quatro medições válidas.

## Referências normativas

- **SAE J443_202512** — *Procedures for Determining and Verifying Peening Intensity*.
- **SAE J2597_201709** — *Computer Generated Shot Peening Saturation Curves*.

As referências são exibidas de forma permanente no aplicativo e na tela de configurações. O sistema não declara conformidade automática: ela depende também da validação do processo, do equipamento e dos dados de ensaio.

## Tabelas técnicas de mídia

O botão **Tabelas técnicas** abre uma tela independente, organizada em três abas:

- roteiro de **análise de esferas** e mídia metálica;
- **granulometria** das designações S70 a S780, com abertura nominal em polegadas e milímetros;
- **tipos de mídia** e normas de referência, incluindo SAE J444, J827, J2175, J441, J445, J442, J443, J2277 e J2597.

Os dados servem como referência de consulta. A aceitação de lote deve sempre seguir a revisão vigente da norma, certificado do fornecedor, desenho e procedimento aprovado.

## Configurações

O botão **Configurações** permite selecionar a unidade da altura da flecha entre milímetros e polegadas. Quando a unidade é alterada, as medições exibidas são convertidas automaticamente, preservando a medida física. A mesma tela também registra o tipo de lâmina Almen e a unidade de exposição usada no ensaio.

Em **Desvios individuais por lâmina**, é possível adicionar e remover dinamicamente quantas lâminas forem necessárias, atribuindo uma identificação e o respectivo desvio. Em cada linha de medição, selecione a lâmina correspondente; o app subtrai somente aquele desvio da flecha daquela linha no cálculo e no gráfico. A opção **Sem desvio** permanece disponível para medições que não precisem de compensação.

Informe cada desvio como **medição indicada − valor real**: por exemplo, `+0,005 mm` significa que a leitura está 0,005 mm acima do valor real. Ao trocar entre mm e polegadas, as flechas e todos os desvios cadastrados são convertidos automaticamente. As medições originalmente digitadas são mantidas.

## Instalação e execução

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Testes

```powershell
python -m unittest discover -s tests -v
```
