import sys

#Coleta informacoes de cada linha dentro do bloco DANC MUDA e retorno um dicionario com todas informacoes.
# Ex line:001 100.00                                        
def getdancInformacoesDaLinha(line):
    try:
        dancInfoLine = {
            'Area': line[0:3].strip(),
            'Fator-Correcao': line[4:10].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dancInfoLine, None


# Responsavel por coletar informacoes do patamar
class coletaBlocosArquivosPatamar:
    def __init__(self, arquivoPatamar):
        self.arquivoPatamar = arquivoPatamar
        self.varreArquivoPatamar()
    
    def varreArquivoPatamar(self):
        try:
            # Abrindo arquivo relacionado ao estagio, ex: 'Diretorio/pat01.afp', 
            with open(self.arquivoPatamar,'r', encoding='latin-1') as arquivo:
                self.arquivoBaseLido = arquivo.readlines()

            danc = False

            respCompletaBlocosInfoBase = {}
            dancInfoBase = {}

            # Varrendo arquivo
            for line in self.arquivoBaseLido:

                if 'DANC MUDA' in line: # Encontrou bloco DANC MUDA
                    danc = True
                    continue            
                else:
                    pass
                
                # Tratamento bloco DANC MUDA
                # Bloco contendo fatores de correcao para aplicacao as cargas das barra, permitindo que se diferencie as cargas para os periodes relacionados a um mesmo caso-base.
                if danc:
                    if line.startswith('99999'): # Terminou Bloco DANC MUDA
                        danc = False
                        continue

                    dancInfoLine, error = getdancInformacoesDaLinha(str(line))
                    if error: sys.exit()
                    area = dancInfoLine['Area']

                    try: int(area) # Tentando evitar que armazene algo diferente de algarismos em area
                    except: continue
                    
                    dancInfoBase[area] = dancInfoLine

            # Armazenando nos atributos da Classe coletaBlocosArquivoBase, dicionarios com as informacoes de cada bloco
            self.dancInfoBase = dancInfoBase

            # Armazenando no atributo respCompletaBlocosInfoBase da classe coletaBlocosArquivoBase, um dicionario contendo os dicionarios de cada bloco obtido
            respCompletaBlocosInfoBase['dancInfoBase'] = self.dancInfoBase

            # Atributo contendo dicionario geral com todos dicionarios de cada bloco obtidos do caso base
            self.respCompletaBlocosInfoBase = respCompletaBlocosInfoBase

        except Exception as error:
            print(error)
            sys.exit()







