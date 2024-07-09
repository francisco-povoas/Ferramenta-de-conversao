import sys

#Coleta informacoes dentro do array com as informacoes da linha da usina Hidraulica.
# Ex linearray: ['  1 ', '   LEVE ', '  1 ', ' CAMARGOS     ', ' SE ', '  99 ', '   99  ', '      0.00 ', '    264.24 ', '     39.32 ', '     67.00 ', '      0.12 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.08 ', '      0.00 ', '      0.20  ', '      0.00  ', '    181.43 ', '      0.33 ', '      0.00 ', '      0.00 ', '    205.75 ', '      0.37 ', '    205.75 ', '      0.37 ', '    778.59 ', '      1.40 ', '     28.49 ', '      46.00 ', '      46.00 ', '  -  ', '      0.00 ', '     20.21 ']
def getusinaHInformacoesDalinha(linearray):
    try:
        hidroInfoLine = {
            'Estagio': linearray[0].strip(),
            'Patamar': linearray[1].strip(),
            'Usina': linearray[3].strip(),
            'Sistema': linearray[4].strip(),
            'Vagua-MWh': linearray[7].strip(),
            'Geracao-MW':linearray[32].strip(),
            'Geracao-Maxima-MW':linearray[33].strip(),
            'Geracao-Minima-MW': '0.00', # Valor arbitrado, Não possui informação no arquivo
            'Capacidade-MW':linearray[34].strip(),
            'Tipo': 'H',
        }
    except Exception as error:
        print(error)
        return None, error
    return hidroInfoLine, None

#Coleta informacoes dentro do array com as informacoes da linha da usina Termoeletrica.
# Ex linearray: ['  1 ', '  LEVE ', '  1 ', 'ANGRA 1      ', '  1 ', ' SE ', '      0.00 ', '      0.00 ', '      0.00 ', '     640.00 ', '  D  ', '     31.17 ']
def getusinaTInformacoesDalinha(linearray):
    try:
        termoInfoLine = {
            'Estagio': linearray[0].strip(),
            'Patamar': linearray[1].strip(),
            'Usina': linearray[3].strip(),
            'Sistema': linearray[5].strip(),
            'Geracao-MW':linearray[6].strip(),
            'Geracao-Minima-MW': linearray[7].strip(),
            'Geracao-Maxima-MW':linearray[8].strip(),
            'Capacidade-MW':linearray[9].strip(),
            'Tipo': 'T',
        }
    except Exception as error:
        print(error)
        return None, error
    return termoInfoLine, None

# Responsavel por coletar informacoes referente a geracao das Usinas Hidraulicas para determinado estagio
class coletaDadosUsinas:
    def __init__(self, arquivoUsinaHidraulica, arquivoUsinaTermoeletrica, estagio):
        self.estagio = int(estagio)

        self.arquivoUsinaHidraulica = arquivoUsinaHidraulica
        self.arquivoUsinaTermoeletrica = arquivoUsinaTermoeletrica

        self.varreArquivoUsinaHidraulica()
        self.varreArquivoUsinaTermoeletrica()

    def varreArquivoUsinaHidraulica(self):
        try:
            # Abrindo arquivo relacionado ao estagio, ex: 'pdo_hidr.dat', 
            with open(self.arquivoUsinaHidraulica,'r', encoding='latin-1') as arquivo:
                self.arquivoUsinaHidraulicaLido = arquivo.readlines()

            periodo = False
            usinaInfoHidraulica = {}

            # Varrendo arquivo
            for line in self.arquivoUsinaHidraulicaLido:
            
                if 'IPER;' in line: # Encontrou bloco IPER
                    periodo = True
                    continue
                
                if periodo and line.startswith('----;'):
                    # Pulando linha imediata de IPER
                    continue
                
                if periodo:

                    periodo = int(line[0:4].strip())

                    if periodo == self.estagio:
                        infoLineArray = str(line).split(';')
                        infoLineArray.pop() # remove ultimo indice nao aproveitavel

                        if '99' in infoLineArray[5]: # verificando se CONJ == 99
                            # Ex usinaInfoHidraulicaLine = {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'PIMENTAL', 'Sistema': 'N', 'Geracao-MW': '79.34', 'Geracao-Maxima-MW': '233.10', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '233.10'}, 'FOZ R. CLARO': {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'FOZ R. CLARO', 'Sistema': 'SE', 'Geracao-MW': '6.92', 'Geracao-Maxima-MW': '34.20', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '68.40'}}
                            usinaInfoHidraulicaLine, error = getusinaHInformacoesDalinha(infoLineArray)
                            if error: sys.exit()

                            usina = usinaInfoHidraulicaLine['Usina']
                            usinaInfoHidraulica[usina] = usinaInfoHidraulicaLine

                    elif (periodo > self.estagio):
                        break
                    else:
                        continue
                  
        except Exception as error:
            print(error)
            sys.exit()

        self.infoUsinaHidraulica = usinaInfoHidraulica

    def varreArquivoUsinaTermoeletrica(self):
        try:
            # Abrindo arquivo relacionado ao estagio, ex: 'pdo_hidr.dat', 
            with open(self.arquivoUsinaTermoeletrica,'r', encoding='latin-1') as arquivo:
                self.arquivoUsinaTermoeletricaLido = arquivo.readlines()

            periodo = False
            usinaInfoTermoeletrica = {}

            # Varrendo arquivo
            for line in self.arquivoUsinaTermoeletricaLido:
            
                if 'IPER;' in line: # Encontrou bloco IPER
                    periodo = True
                    continue
                
                if periodo and (line.startswith('    ;') or line.startswith('----;')) :
                    # Pulando duas linhas imediatamente apos IPER
                    continue
                
                if periodo:
                    periodo = int(line[0:4].strip())

                    if periodo == self.estagio:
                        
                        infoLineArray = str(line).split(';')
                        infoLineArray.pop() # remove ultimo indice nao aproveitavel

                        # Capturando CVU $/MWh
                        if not '99' in infoLineArray[4]:
                            try: custoLinear = infoLineArray[11]
                            except: custoLinear = '0.00'

                        if '99' in infoLineArray[4]: # verificando se Unid == 99
    
                            # Ex usinaInfoHidraulicaLine = {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'PIMENTAL', 'Sistema': 'N', 'Geracao-MW': '79.34', 'Geracao-Maxima-MW': '233.10', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '233.10'}, 'FOZ R. CLARO': {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'FOZ R. CLARO', 'Sistema': 'SE', 'Geracao-MW': '6.92', 'Geracao-Maxima-MW': '34.20', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '68.40'}}
                            usinaInfoTermoeletricaLine, error = getusinaTInformacoesDalinha(infoLineArray)
                            if error: sys.exit()

                            usinaInfoTermoeletricaLine['Custo-Linear-MWh'] = custoLinear

                            usina = usinaInfoTermoeletricaLine['Usina']

                            usinaInfoTermoeletrica[usina] = usinaInfoTermoeletricaLine

                if periodo > self.estagio:
                    break        
                
        except Exception as error:
            print(error)
            sys.exit()
        self.infoUsinaTermoeletrica = usinaInfoTermoeletrica