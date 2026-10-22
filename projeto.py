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
    df = pd.read_csv('Base Varejo.csv', sep=';', parse_dates=['DATA'], dayfirst=True)
    # Remove empty columns created by the trailing ';;;;' in each line
    return df.dropna(axis=1, how='all')


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
    MostrarInfo(df)
