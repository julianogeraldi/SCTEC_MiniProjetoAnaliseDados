import pandas as pd
import zipfile


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


if __name__ == "__main__":
    # Load the dataset
    df = VerificarArquivoBase()
    df = LimparDados(df)
    MostrarInfo(df)
