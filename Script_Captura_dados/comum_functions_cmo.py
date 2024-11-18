import sys

#Coleta informacoes dentro do array com as informacoes de cmo da barra.
# Ex linearray: ['   1  ', '   LEVE', ' 43965 ', 'SPU-T3-BA013 ', '  NE   ', '        0.01 ']
def getCmoInformacoesDalinha(linearray):
    try:
        cmoInfoLine = {
            'Estagio': linearray[0].strip(),
            'Patamar': linearray[1].strip(),
            'Numero-Barra': linearray[2].strip(),
            'Nome-Barra': linearray[3].strip(),
            'Subsistema': linearray[4].strip(),
            'Custo-Marginal': linearray[5].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return cmoInfoLine, None

# Responsavel por coletar informacoes do CUSTO MARGINAL DE OPERACAO
class coletaDadosCmoBarras:
    def __init__(self, arquivoCmo, estagio):
        self.estagio = int(estagio)

        self.arquivoCmo = arquivoCmo
        self.varreArquivoCmo()

    def varreArquivoCmo(self):
        try:
            # Abrindo arquivo relacionado ao estagio, ex: 'pdo_cmobar.dat', 
            with open(self.arquivoCmo,'r', encoding='latin-1') as arquivo:
                self.arquivoCmoLido = arquivo.readlines()

            periodo = False
            cmoInfo = {}

            # Varrendo arquivo
            for line in self.arquivoCmoLido:
            
                if 'IPER ;' in line: # Encontrou bloco IPER
                    periodo = True
                    continue
                
                if periodo and line.startswith('------;'):
                    # Pulando linha imediata de IPER
                    continue
                
                if periodo:

                    periodo = int(line[0:4].strip())

                    if periodo == self.estagio:
                        infoLineArray = str(line).split(';')
                        infoLineArray.pop() # remove ultimo indice nao aproveitavel

                        # Ex CmoInfoLine = {'Estagio': '1', 'Patamar': 'LEVE', 'Numero-Barra': '10', 'Nome-Barra': 'ANGRA1UNE000', 'Subsistema': 'SE', 'Custo-Marginal': '0.01' }
                        CmoInfoLine, error = getCmoInformacoesDalinha(infoLineArray)
                        if error: sys.exit()

                        barra = CmoInfoLine['Numero-Barra']
                        cmoInfo[barra] = CmoInfoLine

                    elif (periodo > self.estagio):
                        break
                    else:
                        continue
                  
        except Exception as error:
            print(error)
            sys.exit()

        self.infoCmo = cmoInfo