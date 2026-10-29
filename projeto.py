import pandas as pd
import zipfile
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Cores do dashboard
COR_1 = '#2a78d6'
COR_2 = '#e8743b'
TEXTO = '#52514e'
GRADE = '#e5e5e3'
GENEROS = {'F': 'Feminino', 'M': 'Masculino'}


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

    return filhos, estatisticas


def PadroesAgrupamento(df):
    # A base não tem valor nem quantidade, então cada linha conta como um item
    # vendido e cada CO_ID distinto como uma compra.

    # Agrupamento 1 - groupby: compras, itens e clientes por gênero
    por_genero = df.groupby('CL_GENERO', observed=True).agg(
        compras=('CO_ID', 'nunique'),
        itens_vendidos=('PR_ID', 'size'),
        clientes=('CL_ID', 'nunique'),
    )
    por_genero['itens_por_compra'] = por_genero['itens_vendidos'] / por_genero['compras']
    por_genero['compras_por_cliente'] = por_genero['compras'] / por_genero['clientes']
    por_genero['pct_compras'] = por_genero['compras'] / por_genero['compras'].sum() * 100
    print("\nCompras por gênero:")
    print(por_genero.round(2).to_string())
    genero_top = por_genero['compras'].idxmax()
    print(f"Gênero com mais compras: {GENEROS[genero_top]} "
          f"({por_genero.loc[genero_top, 'pct_compras']:.1f}% das compras)")

    # Agrupamento 2 - pivot_table: itens vendidos por categoria x gênero
    por_categoria = df.pivot_table(index='PR_CAT', columns='CL_GENERO', values='CO_ID',
                                   aggfunc='size', observed=True)
    por_categoria['Total'] = por_categoria.sum(axis=1)
    por_categoria = por_categoria.sort_values('Total', ascending=False)
    print("\nItens vendidos por categoria e gênero:")
    print(por_categoria.to_string())

    return por_genero, por_categoria


def GerarDashboard(filhos, estatisticas, por_genero, por_categoria):
    fig, eixos = plt.subplot_mosaic(
        [['barras', 'box'], ['cards', 'cards'], ['categorias', 'genero']],
        figsize=(12, 14), width_ratios=[2, 1], height_ratios=[3, 2, 3])

    # Visualização: distribuição (barras, pois a variável é discreta) e boxplot
    ax_barras, ax_box = eixos['barras'], eixos['box']

    contagem = filhos.value_counts().sort_index()
    barras = ax_barras.bar(contagem.index, contagem.values, color=COR_1, width=0.6)
    ax_barras.bar_label(barras, padding=3, color=TEXTO)
    # Espaço acima das barras para as linhas não cruzarem os rótulos
    ax_barras.set_ylim(0, contagem.max() * 1.15)
    ax_barras.axvline(estatisticas['Média'], ymax=0.85, color=TEXTO, linestyle='--',
                      linewidth=1.5, label=f"Média ({estatisticas['Média']:.2f})")
    ax_barras.axvline(estatisticas['Mediana'], ymax=0.85, color=TEXTO, linestyle=':',
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
                   boxprops={'facecolor': COR_1, 'alpha': 0.35, 'color': COR_1},
                   medianprops={'color': COR_1, 'linewidth': 2},
                   whiskerprops={'color': TEXTO}, capprops={'color': TEXTO})
    ax_box.set_title('Boxplot (quartis)')
    ax_box.set_ylabel('Número de filhos')
    ax_box.set_xticks([])
    ax_box.set_yticks(range(int(filhos.min()), int(filhos.max()) + 1))

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
                      color=TEXTO, fontsize=10, va='center')
        ax_cards.text(x + 0.015, y + altura * 0.48, f'{valor:g}', transform=ax_cards.transAxes,
                      color='#0b0b0b', fontsize=20, fontweight='bold', va='center')
        ax_cards.text(x + 0.015, y + altura * 0.17, legenda, transform=ax_cards.transAxes,
                      color=TEXTO, fontsize=9, va='center')

    # Itens vendidos por categoria e gênero (barras horizontais agrupadas)
    ax_cat = eixos['categorias']
    categorias = por_categoria.index[::-1]  # maior categoria no topo
    posicoes = range(len(categorias))
    espessura = 0.38
    for deslocamento, genero, cor in ((espessura / 2, 'F', COR_1), (-espessura / 2, 'M', COR_2)):
        valores = por_categoria.loc[categorias, genero]
        barras_cat = ax_cat.barh([p + deslocamento for p in posicoes], valores,
                                 height=espessura - 0.04, color=cor, label=GENEROS[genero])
        ax_cat.bar_label(barras_cat, labels=[f'{v / 1000:.0f} mil' for v in valores],
                         padding=3, color=TEXTO, fontsize=8)
    ax_cat.set_yticks(list(posicoes), [c.capitalize() for c in categorias])
    ax_cat.set_xlim(0, por_categoria[['F', 'M']].max().max() * 1.12)
    ax_cat.xaxis.set_major_formatter(lambda v, _: f'{v / 1000:.0f} mil')
    ax_cat.set_title('Itens vendidos por categoria e gênero')
    ax_cat.set_xlabel('Itens vendidos')
    ax_cat.legend(frameon=False, loc='lower right')
    ax_cat.grid(axis='x', color=GRADE, linewidth=0.8)

    # Compras por gênero
    ax_gen = eixos['genero']
    nomes = [GENEROS[g] for g in por_genero.index]
    barras_gen = ax_gen.bar(nomes, por_genero['compras'], color=[COR_1, COR_2], width=0.55)
    ax_gen.bar_label(barras_gen, padding=3, color=TEXTO,
                     labels=[f"{c:,.0f}".replace(',', '.') + f"\n({p:.1f}%)"
                             for c, p in zip(por_genero['compras'], por_genero['pct_compras'])])
    ax_gen.set_ylim(0, por_genero['compras'].max() * 1.2)
    ax_gen.set_title('Compras por gênero')
    ax_gen.set_ylabel('Número de compras')
    ax_gen.grid(axis='y', color=GRADE, linewidth=0.8)
    ax_gen.text(0.5, -0.14, 'Itens por compra: ' + ' · '.join(
        f"{GENEROS[g]} {v:.1f}" for g, v in por_genero['itens_por_compra'].items()),
        transform=ax_gen.transAxes, ha='center', color=TEXTO, fontsize=9)

    for ax in (ax_barras, ax_box, ax_cat, ax_gen):
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_axisbelow(True)
    for ax in (ax_barras, ax_box):
        ax.grid(axis='y', color=GRADE, linewidth=0.8)

    fig.tight_layout()
    fig.savefig('estatisticas_filhos.png', dpi=120)
    plt.show()


if __name__ == "__main__":
    # Load the dataset
    df = VerificarArquivoBase()
    df = LimparDados(df)
    MostrarInfo(df)
    filhos, estatisticas = EstatisticasFilhos(df)
    por_genero, por_categoria = PadroesAgrupamento(df)
    GerarDashboard(filhos, estatisticas, por_genero, por_categoria)
