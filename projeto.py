import pandas as pd 
import zipfile




def VerificarArquivoBase():
    try:
        # Attempt to read the CSV file
        df = pd.read_csv('Base Varejo.csv')
        print("Arquivo carregado com sucesso!")
        return df
    except FileNotFoundError:
        with zipfile.ZipFile('BaseVarejo.csv.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
            df = pd.read_csv('Base Varejo.csv')
            print("Arquivo carregado com sucesso!")
            return df





if __name__ == "__main__":
    # Load the dataset
    df = VerificarArquivoBase()