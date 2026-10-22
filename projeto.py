import pandas as pd
import zipfile
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


def MostrarInfo(df):
    # Display the number of records and columns
    print(f"Número de registros: {df.shape[0]}")
    print(f"Número de colunas: {df.shape[1]}")

    # Display the column names
    print("\nColunas:")
    print(df.columns.tolist())

    # Display the data types of each column
    print("\nTipos de dados:")
    print(df.dtypes)

    # Display the first few rows of the DataFrame
    print("\nPrimeiras linhas do DataFrame:")
    print(df.head())

    # Display information about the DataFrame
    print("\nInformações do DataFrame:")
    df.info()

    # Display summary statistics of the DataFrame
    print("\nEstatísticas do DataFrame:")
    print(df.describe())


def LerCSV():
    return pd.read_csv('Base Varejo.csv', sep=';')


def LimparDados(df):
    df = df.copy()

    # Etapa 1 - Nulos
    # Remove as colunas vazias criadas pelos ';;;;' no fim de cada linha
    df = df.dropna(axis=1, how='all')
    # '#N/D' é um nulo "disfarçado" (erro de PROCV do Excel). Aparece em PR_CAT e
    # PR_NOME, sempre no produto PR_ID 107, então não dá para descobrir o valor real
    # a partir de outras linhas. Optamos por IMPUTAR 'NAO IDENTIFICADO' em vez de
    # remover: as linhas têm data, compra e cliente válidos, e excluí-las
    # distorceria análises de clientes e de compras. O produto continua
    # identificável e pode ser filtrado em análises por produto ou categoria.
    df = df.replace('#N/D', pd.NA)
    nulos = df.isna().sum()
    print(f"Nulos encontrados:\n{nulos[nulos > 0]}")
    df[['PR_CAT', 'PR_NOME']] = df[['PR_CAT', 'PR_NOME']].fillna('NAO IDENTIFICADO')

    # Etapa 2 - Duplicatas
    # Linhas idênticas em todas as colunas (mesma compra, cliente e produto) são
    # tratadas como registros repetidos, já que a base não tem coluna de quantidade.
    duplicadas = df.duplicated().sum()
    print(f"Duplicatas removidas: {duplicadas}")
    df = df.drop_duplicates().reset_index(drop=True)

    # Etapa 3 - Tipos de dados
    df['DATA'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y')
    for coluna in ['CL_GENERO', 'CL_SEG', 'PR_CAT', 'PR_NOME']:
        df[coluna] = df[coluna].astype('category')

    return df


def VerificarArquivoBase():
    try:
        # Attempt to read the CSV file
        df = LerCSV()
        print("Arquivo carregado com sucesso!")
        return df
    except FileNotFoundError:
        with zipfile.ZipFile('BaseVarejo.csv.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
            df = LerCSV()
            print("Arquivo carregado com sucesso!")
            return df


def EstatisticasFilhos(df):
    # Cada linha é um item comprado, então o mesmo cliente aparece várias vezes.
    # Para não dar mais peso a quem compra mais, as estatísticas usam um registro
    # por cliente (CL_FHL é fixo para cada CL_ID).
    filhos = df.drop_duplicates('CL_ID')['CL_FHL']

    estatisticas = pd.Series({
        'Contagem': filhos.count(),
        'Média': filhos.mean(),
        'Mediana': filhos.median(),
        'Desvio padrão': filhos.std(),
        'Moda': filhos.mode().iloc[0],
        'Mínimo': filhos.min(),
        '1º quartil (25%)': filhos.quantile(0.25),
        '2º quartil (50%)': filhos.quantile(0.50),
        '3º quartil (75%)': filhos.quantile(0.75),
        'Máximo': filhos.max(),
    })
    print("\nEstatísticas descritivas - número de filhos por cliente:")
    print(estatisticas.round(2).to_string())

    # Visualização: distribuição (barras, pois a variável é discreta) e boxplot
    cor = '#2a78d6'
    texto = '#52514e'
    fig, eixos = plt.subplot_mosaic([['barras', 'box'], ['cards', 'cards']], figsize=(12, 9),
                                    width_ratios=[2, 1], height_ratios=[3, 2])
    ax_barras, ax_box = eixos['barras'], eixos['box']

    contagem = filhos.value_counts().sort_index()
    barras = ax_barras.bar(contagem.index, contagem.values, color=cor, width=0.6)
    ax_barras.bar_label(barras, padding=3, color=texto)
    # Espaço acima das barras para as linhas não cruzarem os rótulos
    ax_barras.set_ylim(0, contagem.max() * 1.15)
    ax_barras.axvline(estatisticas['Média'], ymax=0.85, color=texto, linestyle='--',
                      linewidth=1.5, label=f"Média ({estatisticas['Média']:.2f})")
    ax_barras.axvline(estatisticas['Mediana'], ymax=0.85, color=texto, linestyle=':',
                      linewidth=1.5, label=f"Mediana ({estatisticas['Mediana']:.0f})")
    # Entradas só de texto na legenda, sem marca no gráfico
    ax_barras.plot([], [], ' ', label=f"Desvio padrão: {estatisticas['Desvio padrão']:.2f}")
    ax_barras.plot([], [], ' ', label=f"Total de clientes: {estatisticas['Contagem']:.0f}")
    ax_barras.set_title('Distribuição do número de filhos')
    ax_barras.set_xlabel('Número de filhos')
    ax_barras.set_ylabel('Quantidade de clientes')
    ax_barras.set_xticks(contagem.index)
    ax_barras.legend(frameon=False)

    ax_box.boxplot(filhos, widths=0.4, patch_artist=True,
                   boxprops={'facecolor': cor, 'alpha': 0.35, 'color': cor},
                   medianprops={'color': cor, 'linewidth': 2},
                   whiskerprops={'color': texto}, capprops={'color': texto})
    ax_box.set_title('Boxplot (quartis)')
    ax_box.set_ylabel('Número de filhos')
    ax_box.set_xticks([])
    ax_box.set_yticks(range(int(filhos.min()), int(filhos.max()) + 1))

    for ax in (ax_barras, ax_box):
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', color='#e5e5e3', linewidth=0.8)
        ax.set_axisbelow(True)

    # Cartões com as estatísticas que não aparecem no gráfico de barras
    cards = [
        ('Mínimo', estatisticas['Mínimo'], 'Menor valor'),
        ('1º quartil', estatisticas['1º quartil (25%)'], '25% dos clientes têm até'),
        ('Moda', estatisticas['Moda'], 'Valor mais frequente'),
        ('3º quartil', estatisticas['3º quartil (75%)'], '75% dos clientes têm até'),
        ('Máximo', estatisticas['Máximo'], 'Maior valor'),
        ('Desvio padrão', round(estatisticas['Desvio padrão'], 2), 'Dispersão'),
        ('Total de clientes', estatisticas['Contagem'], 'Observações'),
    ]
    ax_cards = eixos['cards']
    ax_cards.axis('off')
    colunas, linhas = 4, 2
    largura, altura, espaco = 0.24, 0.44, 0.0133
    for i, (titulo, valor, legenda) in enumerate(cards):
        x = (i % colunas) * (largura + espaco)
        y = (linhas - 1 - i // colunas) * (altura + 0.1) + 0.01
        ax_cards.add_patch(FancyBboxPatch((x, y), largura, altura,
                                          boxstyle='round,pad=0,rounding_size=0.03',
                                          transform=ax_cards.transAxes, facecolor='#fcfcfb',
                                          edgecolor='#d9d9d6', linewidth=1))
        ax_cards.text(x + 0.015, y + altura * 0.8, titulo, transform=ax_cards.transAxes,
                      color=texto, fontsize=10, va='center')
        ax_cards.text(x + 0.015, y + altura * 0.48, f'{valor:g}', transform=ax_cards.transAxes,
                      color='#0b0b0b', fontsize=20, fontweight='bold', va='center')
        ax_cards.text(x + 0.015, y + altura * 0.17, legenda, transform=ax_cards.transAxes,
                      color=texto, fontsize=9, va='center')

    fig.tight_layout()
    fig.savefig('estatisticas_filhos.png', dpi=120)
    plt.show()

    return estatisticas


if __name__ == "__main__":
    # Load the dataset
    df = VerificarArquivoBase()
    df = LimparDados(df)
    MostrarInfo(df)
    EstatisticasFilhos(df)
