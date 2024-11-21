import sys

# Coleta informacoes de cada linha dentro do bloco DBAR e retorno um dicionario com todas informacoes.
# Ex line:    10 L1 VANGRA1UNE000 5 976105.     795.4   0.   0.        32. 15.5     2211000                  1                
def getdbarInformacoesDaLinha(line):
    try:
        dbarInfoLine = {
            'Numero': line[0:5].strip(), # BUS_I ok
            'Operacao': line[5].strip(),
            'Estado':line[6].strip(),
            'Tipo': line[7].strip(), # BUS_TYPE ok
            'Grupo-De-Base-De-Tensao': line[8:10].strip(),  # grupo bloco DGBT
            'Nome': line[10:22].strip(),
            'Grupo-Limite-De-Tensao': line[22:24].strip(), # Grupo bloco DGLT
            'Tensao': line[24:28].strip(),
            'Angulo': line[28:32].strip(),
            'Geracao-Ativa':line[32:37].strip(),
            'Geracao-Reativa': line[37:42].strip(),
            'Geracao-Reativa-Minima': line[42:47].strip(),
            'Geracao-Reativa-Maxima':line[47:52].strip(),
            'Barra-Controlada': line[52:58].strip(),
            'Carga-Ativa' : line[58:63].strip(),
            'Carga-Reativa': line[63:68].strip(),
            'Capacitor-Reator': line[68:73].strip(),
            'Area': line[73:76].strip(),
            'Numero-Submercado':line[96:100].strip(), 
        }
    except Exception as error:
        print(error)
        return None, error
    return dbarInfoLine, None 

# Coleta informacoes de cada linha dentro do bloco DLIN e retorno um dicionario com todas informacoes.
# Ex line:   27        87 1     .051  .782  66.5                          18552337  2337                                
def getdlinInformacoesDaLinha(line):
    try:
        dlinInfoLine = {
            'Barra-De': line[0:5].strip(),
            'Situacao-Da-Barra-De': line[5].strip(),
            'Codigo-Operacao':line[7].strip(),
            'Situacao-Da-Barra-Para': line[9].strip(),
            'Barra-Para': line[10:15].strip(),
            'Circuito-Paralelo': line[15:17].strip(),
            'Estado': line[17].strip(),
            'Propriedade': line[18].strip(),
            'Resistencia': line[20:26].strip(),
            'Reatancia':line[26:32].strip(),
            'Susceptancia': line[32:38].strip(),
            'Tap': line[38:43].strip(),
            'Angulo-Defasagem':line[53:58].strip(),
            'Capacidade-Fluxo-Circuito-Condicoes-Normais': line[64:68].strip(),
            'Capacidade-Fluxo-Circuito-Condicoes-Emergencia': line[68:72].strip(),
            'Flag-Permissao-De-Violacao-Fluxo-Circuito' : line[96].strip(),
            'Flag-Consideracao-De-Perdas-Circuito' : line[98].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dlinInfoLine, None

# Coleta informacoes de cada linha dentro do bloco DGLT e retorno um dicionario com todas informacoes.
# Ex line: 5   .95  1.05    .9  1.05
def getdgltInformacoesDaLinha(line):
    try:
        dgltInfoLine = {
            'Grupo': line[0:2].strip(), # Identificador do grupo limite de tensao no bloco DBAR
            'Limite-Minimo': line[3:8].strip(),
            'Limite-Maximo': line[9:14].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dgltInfoLine, None

# Coleta informacoes de cada linha dentro do bloco DGBT e retorno um dicionario com todas informacoes.
# Ex line: V  992.  0
def getdgbtInformacoesDaLinha(line):
    try:
        dgbtInfoLine = {
            'Letra-Identificadora-Grupo-Base': line[0:2].strip(), # Identificador do grupo base de tensao no bloco DBAR
            'Tensao-Nominal-Grupo-Base-KV': line[3:8].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dgbtInfoLine, None

#Coleta informacoes de cada linha dentro do bloco DUSI e retorno um dicionario com todas informacoes.
# Ex line:   1   1168 14 DE JULHO    2                                              991H
def getdusiInformacoesDaLinha(line):
    try:
        dusiInfoLine = {
            'Numero-Identificacao-Elemento-DUSI': line[0:4].strip(),
            'Operacao': line[5].strip(),
            'Numero-Barra-Elemento-Conectado': line[6:11].strip(),
            'Nome-Usina': line[12:24].strip(),
            'Numero-Unidades-Geradoras-Elemento': line[26:29].strip(),
            'Geracao-Ativa-Minima-Cada-Unidade-Geradora-Elemento': line[32:38].strip(),
            'Geracao-Ativa-Maxima-Cada-Unidade-Geradora-Elemento': line[38:44].strip(),
            'Numero-Cadastro-Usina': line[72:76].strip(),
            'Numero-Grupo-Pertencimento-Usina': line[76].strip(),
            'Mnemonico-Identificacao': line[77].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dusiInfoLine, None

#Coleta informacoes de cada linha dentro do bloco DARE e retorno um dicionario com todas informacoes.
# Ex line:   1        0.     RS - 525 kV                                        
def getdareInformacoesDaLinha(line):
    try:
        dareInfoLine = {
            'Area': line[0:4].strip(),
            'Identificacao-Area': line[5].strip(),
        }
    except Exception as error:
        print(error)
        return None, error
    return dareInfoLine, None

# Responsavel por coletar informacoes do caso base
class coletaBlocosArquivoBase:
    def __init__(self, arquivoBase):
        self.arquivoBase = arquivoBase
        self.varreArquivoBase()

    def varreArquivoBase(self):
        try:
            # Abrindo arquivo base 'leve.pwf', 'media.pwf', 'pesada.pwf' para coletar dbar, dlin, dglt, dgbt, dusi
            with open(self.arquivoBase,'r', encoding='latin-1') as arquivo:
                self.arquivoBaseLido = arquivo.readlines()
            
            dbar = False
            dlin = False
            dglt = False
            dgbt = False
            dusi = False
            dare = False

            respCompletaBlocosInfoBase = {}
            dbarInfoBase = {}
            dlinInfoBase = {}
            dgltInfoBase = {}
            dgbtInfoBase = {}
            dusiInfoBase = {}
            dareInfoBase = {}

            # Varrendo arquivo
            for line in self.arquivoBaseLido:

                if 'DBAR' in line: # Encontrou bloco DBAR
                    dbar = True
                    continue
                elif 'DLIN' in line: # Encontrou bloco DLIN
                    dlin = True
                    continue
                elif 'DGLT' in line: # Encontrou bloco DGLT
                    dglt = True
                    continue
                elif 'DGBT' in line: # Encontrou bloco DGBT
                    dgbt = True
                    continue
                elif 'DUSI' in line: # Encontrou bloco DUSI
                    dusi = True
                    continue
                elif 'DARE' in line: # Encontrou bloco DARE
                    dare = True
                    continue                
                else:
                    pass
                
                # Tratamento bloco DBAR
                # Bloco contendo caracteristicas das barras da rede eletrica.
                if dbar:
                    if line.startswith('(Num)'):
                        continue
                    if line.startswith('99999'): # Terminou Bloco DBAR
                        dbar = False
                        continue
                    
                    # Ex dbarInfoLine = {'Numero': '10', 'Operacao': '', 'Estado': 'L', 'Tipo': '1', 'Grupo-De-Base-De-Tensao': 'V', 'Nome': 'ANGRA1UNE000', 'Grupo-Limite-De-Tensao': '5', 'Tensao': '976', 'Angulo': '105.', 'Geracao-Ativa': '', 'Geracao-Reativa': '795.4', 'Geracao-Reativa-Minima': '0.', 'Geracao-Reativa-Maxima': '0.', 'Barra-Controlada': '', 'Carga-Ativa': '32.', 'Carga-Reativa': '15.5', 'Capacitor-Reator': '', 'Area': '221', 'Numero-Submercado': '1'}
                    dbarInfoLine, error = getdbarInformacoesDaLinha(str(line))
                    if error: sys.exit()
                    
                    numero = dbarInfoLine['Numero']
                    dbarInfoBase['barra-'+numero] = dbarInfoLine

                # Tratamento bloco DLIN 
                # Bloco contendo caracteristicas dos circuitos (linhas de transmissao) da rede eletrica.
                if dlin:
                    if line.startswith('(De )'):
                        continue
                    if line.startswith('99999'): # Terminou Bloco DLIN
                        dlin = False
                        continue
                    line = str(line)

                    dlinInfoLine, error = getdlinInformacoesDaLinha(str(line))
                    if error: sys.exit()

                    barraDe = dlinInfoLine['Barra-De']
                    barraPara = dlinInfoLine['Barra-Para']

                    dlinInfoBase['Linha-'+barraDe+'-'+barraPara] = dlinInfoLine

                # Tratamento bloco DGLT
                # Bloco contendo os grupos de limites de tensao que cada barra estah sujeita. Valores em pu, limites max e min.
                if dglt:
                    if line.startswith('(G'):
                        continue
                    if line.startswith('99999'): # Terminou Bloco DGLT
                        dglt = False
                        continue

                    dgltInfoLine, error = getdgltInformacoesDaLinha(str(line))
                    if error: sys.exit()
                    
                    grupo = dgltInfoLine['Grupo']
                    dgltInfoBase[grupo] = dgltInfoLine

                # Tratamento bloco DGBT
                # Bloco contendo niveis diferentes de tensao (denominados de grupos base de tensao) presentes na rede eletrica. Valores aos quais cada barra do sistema tem referenciado seu nivel de tensao em pu.
                if dgbt:
                    if line.startswith('(G'):
                        continue
                    if line.startswith('99999'): # Terminou Bloco DGBT
                        dgbt = False
                        continue
                    
                    dgbtInfoLine, error = getdgbtInformacoesDaLinha(str(line))
                    if error: sys.exit()

                    grupo = dgbtInfoLine['Letra-Identificadora-Grupo-Base']
                    dgbtInfoBase[grupo] = dgbtInfoLine
                
                # Tratamento bloco DUSI
                # Bloco contendo as conexoes das unidades geradoras (hidro, termo e elevatorias) as barras da rede eletrica. Desta forma faz-se o link entre a parte eletrica e a parte energetica do sistema.
                if dusi:
                    if line.startswith('(No)'):
                        continue
                    if line.startswith('99999'): # Terminou Bloco DUSI
                        dusi = False
                        continue
                    
                    # Tratativa para linhas menores que 79 colunas, caso de linhas que podem ser desprezadas dentro do Bloco DUSI
                    if len(str(line)) < 79:
                        continue

                    dusiInfoLine, error = getdusiInformacoesDaLinha(str(line))
                    if error: sys.exit()

                    #Validando o mnemonico obtido, coluna 78 referencia: Centro de Pesquisas de Energia Eletrica - CEPEL Manual do Usuario - Modelo DESSEM v. 19.0.24.3 - Marco/2022
                    # [Se diferente de H=> hidro e T=> termo nao concateno no dusiInfoBase]
                    # Nao concateno mais E=> Elevatorio
                    if ((dusiInfoLine['Mnemonico-Identificacao'] != 'H') and (dusiInfoLine['Mnemonico-Identificacao'] != 'T')):
                        continue
                    
                    numeroIdentificacaoDusi = dusiInfoLine['Numero-Barra-Elemento-Conectado']
                    dusiInfoBase[numeroIdentificacaoDusi] = dusiInfoLine

                # Tratamento bloco DARE
                # Bloco contendo o algarismo e indentificacao das areas da rede eletrica.
                if dare:
                    if line.startswith('(Ar'):
                        continue
                    if line.startswith('99999'): # Terminou bloco DARE
                        dare = False
                        continue

                    dareInfoLine, error = getdareInformacoesDaLinha(str(line))
                    if error: sys.exit()

                    area = dareInfoLine['Area']
                    dareInfoBase[area] = dareInfoLine



            # Armazenando nos atributos da Classe coletaBlocosArquivoBase, dicionarios com as informacoes de cada bloco
            self.dbarInfoBase = dbarInfoBase
            self.dlinInfoBase = dlinInfoBase
            self.dgltInfoBase = dgltInfoBase
            self.dgbtInfoBase = dgbtInfoBase
            self.dusiInfoBase = dusiInfoBase
            self.dareInfoBase = dareInfoBase

            # Armazenando no atributo respCompletaBlocosInfoBase da classe coletaBlocosArquivoBase, um dicionario contendo os dicionarios de cada bloco obtido
            respCompletaBlocosInfoBase['dbarInfoBase'] = self.dbarInfoBase
            respCompletaBlocosInfoBase['dlinInfoBase'] = self.dlinInfoBase
            respCompletaBlocosInfoBase['dgltInfoBase'] = self.dgltInfoBase
            respCompletaBlocosInfoBase['dgbtInfoBase'] = self.dgbtInfoBase
            respCompletaBlocosInfoBase['dusiInfoBase'] = self.dusiInfoBase
            respCompletaBlocosInfoBase['dareInfoBase'] = self.dareInfoBase

            # Atributo contendo dicionario geral com todos dicionarios de cada bloco obtidos do caso base
            self.respCompletaBlocosInfoBase = respCompletaBlocosInfoBase

        except Exception as error:
            print(error)
            sys.exit()