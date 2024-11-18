import sys
from comum_functions import defineEstagio
from comum_functions_base import *
from comum_functions_patamar import *
from comum_functions_usina import *
from comum_functions_cmo import *
from defines import *
import os

class coletaInfoEstagio:
    def __init__(self, estagio):
        
        self.estagio = estagio
        try:
            # Abrindo arquivo principal que informa o arquivo de caso base de acordo com o estagio requirido
            with open(DESSELET_DAT,'r') as arquivo:

                # Arquivos com Dados Eletricos para o DESSEM
                self.arquivoGeral = arquivo.readlines()

            for line in self.arquivoGeral:
                if 'Estagio'+self.estagio in line:
                    # Amazenando informacoes do estagio, descartando apenas TIME
                    ### (Id Patamar) YYYYMMDD HH MM TIME T Base (Nome arquivo patamar)
                    # 01 Estagio01    20210520  0  0  0.5      1 pat01.afp

                    # Ex .: infoEstagio = ['01', 'Estagio01', '20210520', '0', '0', '0.5', '1', 'pat01.afp']
                    infoEstagio = line.strip().split()
                    self.id = infoEstagio[0]
                    self.patamar = infoEstagio[1]
                    self.anoMesDia = infoEstagio[2]
                    self.hora = infoEstagio[3]
                    self.minuto = infoEstagio[4]
                    self.base = infoEstagio[6]
                    self.arquivoPatamar = infoEstagio[7] # Alteracoes do caso base

                    arquivoCasoBase = {
                        "1" : LEVE_PWF,
                        "2" : MEDIA_PWF,
                        "3" : PESADA_PWF,
                    }
                
                    self.arquivoBase = arquivoCasoBase.get(self.base, None)
                    if self.arquivoBase == None:
                        raise Exception('Nao foi encontrado o arquivo do caso base para o estagio informado')
                    
        except Exception as error:
            print(error)
            sys.exit()

# Responsavel por coletar informacoes do caso base, patamar, usinas( T e H) tratar e gerar arquivos de saida para o MATPOWER
class tratamentoGeralArquivos:
        def __init__(self, hora, minuto):
            
            # Inicializador da Classe responsavel por coletar todas informacoes necessarias:
            self.estagio = defineEstagio(hora, minuto)
            self.informacoesEstagio = coletaInfoEstagio(self.estagio)
            self.arquivoCasoBase = self.informacoesEstagio.arquivoBase    # Ex's .: leve.pwf, media.pwf, pesada.pwf
            self.arquivoPatamar  = CAMINHO+BLOCO_REVISAO+'/'+self.informacoesEstagio.arquivoPatamar # Ex .: Diretorio/pat01.afp
            
            self.informacoesBlocosArquivoBase = coletaBlocosArquivoBase(self.arquivoCasoBase)

            self.informacoesBlocosArquivoPatamar = coletaBlocosArquivosPatamar(self.arquivoPatamar)

            self.informacoesArquivosUsinas = coletaDadosUsinas(USINA_HIDRAULICA, USINA_TERMOELETRICA, self.estagio)

            self.informacoesCmoBarras = coletaDadosCmoBarras(CMO_BARRAS, self.estagio)
            
            self.montandoEstruturaMpcBus()
            self.montandoEstruturaMpcBranch()
            self.montandoEstruturaMpcGen()
            self.montaArquivoMatPower()
            self.escreveArquivoMatPower()

        def montandoEstruturaMpcBus(self):
            self.mpcBus = {}

            # pegando dados para montar bus_data (mpc.bus)
            for chavebarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase']:

                BUS_I = ''
                BUS_TYPE = ''
                PD = ''
                QD = ''
                GS = ''
                BS = ''
                BUS_AREA = ''
                VM = ''
                VA = ''
                BASEKV = ''
                ZONE = ''
                VMAX = ''
                VMIN = ''

                BUS_I    = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Numero']
                BUS_TYPE = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Tipo']
                if BUS_TYPE == '': BUS_TYPE = '0' # Default
                # DESSEM PQ = 0, PV = 1, ref V0 = 2
                # MATPOWER PQ = 1, PV = 2, ref = 3, isolada = 4
                if BUS_TYPE == '0':
                    BUS_TYPE = '1'
                elif BUS_TYPE == '1':
                    BUS_TYPE = '2'
                elif BUS_TYPE == '2':
                    BUS_TYPE = '3'

                BUS_AREA = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Area']
                PD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Ativa']
                QD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Reativa']
                
                try:
                    PD = float(PD)
                except:
                    PD = 0
                
                try:
                    QD = float(QD)
                except:
                    QD = 0
                

                if BUS_AREA in self.informacoesBlocosArquivoPatamar.respCompletaBlocosInfoBase['dancInfoBase']:
                    FATOR_CORRECAO_CARGA = self.informacoesBlocosArquivoPatamar.respCompletaBlocosInfoBase['dancInfoBase'][BUS_AREA]['Fator-Correcao']
                    if FATOR_CORRECAO_CARGA:
                        if PD: PD = float(PD) * (float(FATOR_CORRECAO_CARGA) / 100)
                        if QD: QD = float(QD) * (float(FATOR_CORRECAO_CARGA) / 100)

                GS = '0' # Sem correspondente no pwf
                BS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Capacitor-Reator']
                if BS == '': BS = '0'

                VM = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Tensao'] # Preciso dividir pelo Tensao-Nominal-Grupo-Base-KV do bloco DGBT
                VA = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Angulo']
                
                ZONE = '0' # Sem correspondente no pwf

                Grupo_Limite_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-Limite-De-Tensao'] # Isso nao vai no mpcBus final, mas vou precisar registrar aqui para varrer dglt depois e colocar os limites de V
                if Grupo_Limite_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgltInfoBase']:
                    VMAX = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgltInfoBase'][Grupo_Limite_De_Tensao]['Limite-Maximo']
                    VMIN = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgltInfoBase'][Grupo_Limite_De_Tensao]['Limite-Minimo']
                else:
                    # Para barras sem grupo relacionados no dglt eu seto valores fixos.
                    VMAX = '1.05'
                    VMIN = '0.95'

                Grupo_De_Base_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-De-Base-De-Tensao'] # usado apenas para pegar a tensao base no bloco dgbt
                if Grupo_De_Base_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase']:
                    BASEKV = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase'][Grupo_De_Base_De_Tensao]['Tensao-Nominal-Grupo-Base-KV']

                VM = float(VM)/1000

                self.mpcBus[BUS_I] = {
                    'BUS_I': BUS_I,
                    'BUS_TYPE': BUS_TYPE,
                    'PD': str(round(PD,2)),
                    'QD': str(round(QD,2)),
                    'GS': GS,
                    'BS': BS,
                    'AREA': BUS_AREA ,
                    'VM': str(round(VM,3)),
                    'VA': VA,
                    'BASEKV': BASEKV,
                    'ZONE': ZONE,  
                    'VMAX': VMAX,
                    'VMIN': VMIN,
                }

        def montandoEstruturaMpcBranch(self):
            self.mpcBranch = {}

            # pegando dados para montar bus_data (mpc.bus)
            for linhaFromTo in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase']:

                F_BUS = ''
                T_BUS = ''
                BR_R = ''
                BR_X = ''
                BR_B = ''
                RATE_A = ''
                RATE_B = ''
                RATE_C = ''
                TAP = ''
                ANGLE = ''
                STATUS = ''
                ANGMIN = '-360'
                ANGMAX = '360'

                F_BUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Barra-De']
                T_BUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Barra-Para']
                BR_R = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Resistencia']
                BR_X = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Reatancia']
                BR_B = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Susceptancia']
                RATE_A = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Capacidade-Fluxo-Circuito-Condicoes-Normais']
                RATE_B = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Capacidade-Fluxo-Circuito-Condicoes-Normais']
                RATE_C = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Capacidade-Fluxo-Circuito-Condicoes-Emergencia']
                TAP = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Tap']
                ANGLE = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Angulo-Defasagem']
                STATUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dlinInfoBase'][linhaFromTo]['Estado']

                if not STATUS:
                    STATUS = '1'
                    # circuito ligado
                    pass
                elif STATUS == 'D':
                    # circuito desligado
                    STATUS = '0'
                    pass

                # Se nao encontrou valor preenche com 0
                try: float(TAP)
                except: TAP = '0'

                try: float(ANGLE)
                except: ANGLE = '0'

                # Tentando converter para PU 
                try:
                    BR_R = str(round(float(BR_R)/100,5))
                except Exception as error:
                    BR_R = '0'
                
                try:
                    BR_X = str(round(float(BR_X)/100,5))
                except:
                    BR_X = '0'

                try:
                    BR_B = str(round(float(BR_B)/100,5))
                except:
                    BR_B = '0'

                self.mpcBranch[linhaFromTo] = {
                    'F_BUS': F_BUS,
                    'T_BUS': T_BUS,
                    'BR_R': BR_R, 
                    'BR_X': BR_X,
                    'BR_B': BR_B,
                    'RATE_A': RATE_A,
                    'RATE_B': RATE_B ,
                    'RATE_C': RATE_C,
                    'RATIO': TAP,
                    'ANGLE': ANGLE,
                    'STATUS': STATUS,
                    'ANGMIN': ANGMIN,
                    'ANGMAX': ANGMAX,
                }

        def montandoEstruturaMpcGen(self):
            self.mpcGen = {}
            for chavebarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase']:
                BUS_NAME = ''
                BUS_SUBS = ''
                BUS_CMO = ''
                
                GEN_BUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Numero']
                # print('GEN_BUS = '+ GEN_BUS + ' TYPE = '+ str(type(GEN_BUS)))
                
                if GEN_BUS in self.informacoesCmoBarras.infoCmo:
                    if 'Nome-Barra' in self.informacoesCmoBarras.infoCmo[GEN_BUS] and \
                       'Subsistema' in self.informacoesCmoBarras.infoCmo[GEN_BUS] and \
                       'Custo-Marginal' in self.informacoesCmoBarras.infoCmo[GEN_BUS]:
                        BUS_NAME = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Nome-Barra']
                        BUS_SUBS = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Subsistema']
                        BUS_CMO = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Custo-Marginal']
                
                try: float(BUS_CMO)
                except: BUS_CMO = 0.00
                
                PG = 0.00
                QG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa']
                QMAX = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Maxima']
                QMIN = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Minima']

                try: QG = float(QG)
                except: QG = 0.00

                try: QMAX = float(QMAX)
                except: QMAX = 0.00

                try: QMIN = float(QMIN)
                except: QMIN = 0.00

                VG = ''
                MBASE = 100 # 100 MVA Arbitrado mas posso pegar no BLOCO DCTE
                GEN_STATUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Estado']
                PMAX = 0.00
                PMIN = 0.00
                PC1 = 0.00
                PC2 = 0.00
                QC1MIN = 0.00
                QC1MAX = 0.00
                QC2MIN = 0.00
                QC2MAX = 0.00
                RAMP_AGC = 0.00
                RAMP_10 = 0.00
                RAMP_30 = 0.00
                RAMP_Q = 0.00
                APF = 0.00

                # Tratando estado
                # "L" ou branco => A barra esta ligada;
                # "D" => A barra esta desligada;
                GEN_STATUS = '0' if GEN_STATUS == 'D' else '1'

                VG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Tensao']
                
                Grupo_De_Base_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-De-Base-De-Tensao'] # usado apenas para pegar a tensao base no bloco dgbt
                if Grupo_De_Base_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase']:
                    BASEKV = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase'][Grupo_De_Base_De_Tensao]['Tensao-Nominal-Grupo-Base-KV']

                VG = float(VG)/1000

                # declarando antes do laco for as variaveis de geracao caso nao entre no if que elas sao usadas
                geracaoUsinaHidraulica = 0.00
                geracaoMaximaUsinaHidraulica = 0.00
                geracaoMinimaUsinaHidraulica = 0.00
                geracaoUsinaTermoeletrica = 0.00
                geracaoMaximaUsinaTermoeletrica = 0.00
                geracaoMinimaUsinaTermoeletrica = 0.00
                
                ### MPC GENCOST ####
                custoUsinaHidraulica = 0.00
                custoUsinaTermoeletrica = 0.00
                CVU = 0.00
                ####

                ### MPC GENNAME ####
                TIPO = ''
                ####
                NOME_USINA_CORRETO = ''
                # print(self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'])
                for chaveNumeroBarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase']:

                    if(chaveNumeroBarra == GEN_BUS):
                        
                        # Nome incorreto. precisa ser alterado para o que esta contido dentro de pdo_term e pdo_hidr.
                        # Elevatoria nao vai atualizar, ja que nao trato tipo E... pegarah valores padroes 0.00
                        NOME_USINA_CORRETO = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][chaveNumeroBarra]['Nome-Usina']
                        
                        # TIPO OK
                        TIPO = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][chaveNumeroBarra]['Mnemonico-Identificacao']
                        
                        numeroCadastroUsina = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][chaveNumeroBarra]['Numero-Cadastro-Usina']
                        
                        # Nao somar H com T. dependendo do tipo entra num dos blocos abaixo...
                        # No momento verificado que nao ha injecao na mesma barra proveniente de T e H, no futuro pode mudar...
                        if TIPO == 'H':
                            for usina in self.informacoesArquivosUsinas.infoUsinaHidraulica:
                                if numeroCadastroUsina == self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Numero-Cadastro-Usina']:
                                    geracaoUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-MW']
                                    geracaoMaximaUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-Maxima-MW']
                                    geracaoMinimaUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-Minima-MW']
                                    custoUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Vagua-MWh']
                                    # print('TIPO = '+ TIPO+' NOME_USINA = '+ NOME_USINA_DUSI + '; USINA = '+ self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Usina'] + ' CVU = '+ custoUsinaHidraulica)
                                    NOME_USINA_CORRETO = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Usina']
                                    try: geracaoUsinaHidraulica = float(geracaoUsinaHidraulica)
                                    except: geracaoUsinaHidraulica == 0.0

                                    try: geracaoMaximaUsinaHidraulica = float(geracaoMaximaUsinaHidraulica)
                                    except: geracaoMaximaUsinaHidraulica = 0.0

                                    try: geracaoMinimaUsinaHidraulica = float(geracaoMinimaUsinaHidraulica)
                                    except: geracaoMinimaUsinaHidraulica = 0.0

                                    try: custoUsinaHidraulica = float(custoUsinaHidraulica)
                                    except: custoUsinaHidraulica = 0.0

                                    PG = geracaoUsinaHidraulica
                                    PMAX = geracaoMaximaUsinaHidraulica
                                    PMIN = geracaoMinimaUsinaHidraulica
                                    CVU = custoUsinaHidraulica
                        elif TIPO == 'T':
                            for usina in self.informacoesArquivosUsinas.infoUsinaTermoeletrica:
                                if numeroCadastroUsina == self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Numero-Cadastro-Usina']:
                                    geracaoUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-MW']
                                    geracaoMaximaUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-Maxima-MW']
                                    geracaoMinimaUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-Minima-MW']
                                    custoUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Custo-Linear-MWh']
                                    # print('TIPO = '+ TIPO+' NOME_USINA = '+ NOME_USINA_DUSI + '; USINA = '+ self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Usina']+ ' CVU = '+ custoUsinaTermoeletrica)
                                    NOME_USINA_CORRETO = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Usina']
                                    try: geracaoUsinaTermoeletrica = float(geracaoUsinaTermoeletrica)
                                    except: geracaoUsinaTermoeletrica == 0.0
                                    
                                    try: geracaoMaximaUsinaTermoeletrica = float(geracaoMaximaUsinaTermoeletrica)
                                    except: geracaoMaximaUsinaTermoeletrica = 0.0

                                    try: geracaoMinimaUsinaTermoeletrica = float(geracaoMinimaUsinaTermoeletrica)
                                    except: geracaoMinimaUsinaHidraulica = 0.0

                                    try: custoUsinaTermoeletrica = float(custoUsinaTermoeletrica)
                                    except: custoUsinaTermoeletrica = 0.0

                                    PG = geracaoUsinaTermoeletrica
                                    PMAX = geracaoMaximaUsinaTermoeletrica
                                    PMIN = geracaoMinimaUsinaTermoeletrica
                                    CVU = custoUsinaTermoeletrica
                        else:
                            pass

                # chavebarra = 'barra-10', 'barra-50'....
                self.mpcGen[chavebarra] = {
                'GEN_BUS': GEN_BUS,
                'PG': str(round(PG,2)),
                'QG': str(round(QG,2)),
                'QMAX': str(round(QMAX,2)),
                'QMIN': str(round(QMIN,2)),
                'VG': str(round(VG,3)),
                'MBASE': MBASE,
                'GEN_STATUS': GEN_STATUS,
                'PMAX': str(round(PMAX,2)),
                'PMIN': str(round(PMIN,2)),
                'PC1': PC1,
                'PC2': PC2,
                'QC1MIN': QC1MIN,
                'QC1MAX': QC1MAX ,
                'QC2MIN': QC2MIN ,
                'QC2MAX': QC2MAX,
                'RAMP_AGC': RAMP_AGC,
                'RAMP_10': RAMP_10,
                'RAMP_30': RAMP_30,
                'RAMP_Q': RAMP_Q,
                'APF': APF,
                'CVU': CVU, # Usado no mpc gencost
                'TIPO': TIPO, # Usado no mpc additional data
                'NOME_USINA': NOME_USINA_CORRETO, # Usado no mpc additional data
                'BUS_NAME': BUS_NAME, # Usado no mpc additional data
                'BUS_SUBS': BUS_SUBS, # Usado no mpc additional data
                'BUS_CMO': BUS_CMO, # Usado no mpc additional data
                }
                
        def montaArquivoMatPower(self):
            doisTabEspace = '   '

            # /home/francisco/Documents/TCC2/Projeto/Ferramenta-de-conversao/Resultados_Ferramenta_Computacional_ds_ons_122023_rv0d29/ds_ons_122023_rv0d29_Estagio01.m
            caminhoCompletoArquivo = DIRETORIO_COM_RESULTADOS_DE_SAIDA + BLOCO_REVISAO+'_'+self.informacoesEstagio.patamar.split('.')[0]+'.m'

            # ds_ons_122023_rv0d29_Estagio01.m
            nomeArquivoSaidaComExtensao = caminhoCompletoArquivo.split('/')[-1]

            # ds_ons_122023_rv0d29_Estagio01
            nomeArquivoSaidaSemExtensao = nomeArquivoSaidaComExtensao.replace('.m', '')

            self.arquivoCabecalho = ''
            self.arquivoCabecalho += 'function mpc = '+nomeArquivoSaidaSemExtensao+'\n'

            self.arquivoCabecalho += '% CASO SIN: extraido dos arquivos de dados do DESSEM\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '% CASO SIN: Fluxo de Potencia do SIN extraido de arquivo de dados do DESSEM\n'
            self.arquivoCabecalho += '% Autores Francisco Povoas e Murilo Reolon\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%   MATPOWER\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%% MATPOWER Case Format : Version 2\n'
            self.arquivoCabecalho += 'mpc.version = \'2\';\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%%-----  Power Flow Data  -----%%\n'
            self.arquivoCabecalho += '\n'
            self.arquivoCabecalho += '%% system MVA base\n'
            self.arquivoCabecalho += 'mpc.baseMVA = 100;\n'

            self.arquivoCabecalho += '\n'
            self.arquivobusData = ''
            self.arquivobusData += '%% bus data\n'
            self.arquivobusData += ('%	' + retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_i',8) +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('type',8)   +	
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pd',8)	   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qd',8)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Gs',8)	   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Bs',8)	   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('area',8)   +	
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Vm',8)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Va',8)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('baseKV',8) +	
            retornaStringArrumadaParaEscreverComTamanhoCorreto('zone',8)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Vmax',8)   + 
              'Vmin' +
            '\n')

            self.arquivobusData += 'mpc.bus = [\n'
            
            for BUS in self.mpcBus:
                self.arquivobusData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBus[BUS]['BUS_I']),8)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBus[BUS]['BUS_TYPE']),8)                +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['PD'])),8)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['QD'])),8)      +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['GS'])),8)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['BS'])),8)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBus[BUS]['AREA']),8)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBus[BUS]['VM']),8)                      +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['VA'])),8)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['BASEKV'])),8)   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBus[BUS]['ZONE']),8)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBus[BUS]['VMAX'])),8)     +
                    corrigeNumero(str(self.mpcBus[BUS]['VMIN']))  +
                    ';\n'
                    )

            self.arquivobusData += '];\n'

            self.arquivoGeneratorData = ''
            self.arquivoGeneratorData += '%% generator data\n'
            # self.arquivoGeneratorData += '%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf\n'
            self.arquivoGeneratorData += ('%	' + 	retornaStringArrumadaParaEscreverComTamanhoCorreto('bus',10) +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pg',10)       +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qg',10)       +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qmax',10)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qmin',10)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Vg',10)       +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('mBase',10)    +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('status',10)   +	
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pmax',10)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pmin',10)     +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pc1',10)      +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Pc2',10)	   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qc1min',10)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qc1max',10)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qc2min',10)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('Qc2max',10)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('ramp_agc',10) +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('ramp_10',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('ramp_30',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('ramp_q',10)   +
            'apf'      +
            '\n')
            self.arquivoGeneratorData += 'mpc.gen = [\n'
            
            self.arquivoGeneratorCostData = ''
            self.arquivoGeneratorCostData += '%%----- OPF Data -----%%\n'
            self.arquivoGeneratorCostData += '%% generator cost data\n'
            self.arquivoGeneratorCostData += '%	1	startup	shutdown	n	x1	y1	...	xn	yn\n'
            self.arquivoGeneratorCostData += '%	2	startup	shutdown	n	c(n-1)	...	c0\n'
            self.arquivoGeneratorCostData += 'mpc.gencost = [\n'


            self.arquivoAdditionalData = ''
            self.arquivoAdditionalData += '%% bus additional data\n'
            self.arquivoAdditionalData += ('%	'+retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_i',14)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_name',14)                                      + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_subs',14)                                      + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_cmo',14)                                       + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_type',14)                                      +
            'gen_name\n'
            )
            self.arquivoAdditionalData += 'mpc.busadd = [\n'

            for chavebarra in self.mpcGen:

                # mpcgen
                self.arquivoGeneratorData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['GEN_BUS']),10)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['PG'])),10)         + 
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['QG'])),10)         +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['QMAX'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['QMIN'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['VG']),10)                        +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['MBASE']),10)                     +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['GEN_STATUS']),10)                +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['PMAX'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen[chavebarra]['PMIN'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['PC1']),10)                       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['PC2']),10)                       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['QC1MIN']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['QC1MAX']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['QC2MIN']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['QC2MAX']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['RAMP_AGC']),10)                  +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['RAMP_10']),10)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['RAMP_30']),10)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['RAMP_Q']),10)                    +
                    str(self.mpcGen[chavebarra]['APF'])  +
                    ';\n'
                    )
                
                # mpcgencost
                self.arquivoGeneratorCostData += (
                    doisTabEspace + 
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('2',10)                                 +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('0',10)                                 +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('0',10)                                 +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('2',10)                                 +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['CVU']),10) + 
                    '0' +
                    ';\n'
                    )
                
                # mpcbusadd
                self.arquivoAdditionalData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['GEN_BUS']),14) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['BUS_NAME']),14) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['BUS_SUBS']),14) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['BUS_CMO']),14) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen[chavebarra]['TIPO']),14)    +
                    str(self.mpcGen[chavebarra]['NOME_USINA']) +
                    ';\n'
                    )

            self.arquivoGeneratorData += '];\n'
            self.arquivoGeneratorData += '%\n'

            self.arquivoGeneratorCostData += '];\n'
            self.arquivoGeneratorCostData += '%\n'

            self.arquivoAdditionalData += '];\n'
            self.arquivoAdditionalData += '%\n'

            self.arquivoBranchData = ''
            self.arquivoBranchData += '%% branch data\n'
            # self.arquivoBranchData += '%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax\n'
            self.arquivoBranchData += ('%	' + 	retornaStringArrumadaParaEscreverComTamanhoCorreto('fbus',10) +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('tbus',10)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('r',10)      +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('x',10)      +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('b',10)      +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('rateA',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('rateB',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('rateC',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('ratio',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('angle',10)  +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('status',10) +	
            retornaStringArrumadaParaEscreverComTamanhoCorreto('angmin',10) +
            'angmax' +	
            '\n'
            )

            self.arquivoBranchData += 'mpc.branch = [\n'
            for linhaFromTo in self.mpcBranch:
                self.arquivoBranchData += (
                doisTabEspace +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBranch[linhaFromTo]['F_BUS']),10)                 +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBranch[linhaFromTo]['T_BUS']),10)                 +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['BR_R'])),10)   +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['BR_X'])),10)   +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['BR_B'])),10)   +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['RATE_A'])),10) +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['RATE_B'])),10) +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['RATE_C'])),10) +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcBranch[linhaFromTo]['RATIO'])),10)  +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBranch[linhaFromTo]['ANGLE']),10) +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBranch[linhaFromTo]['STATUS']),10) +
                retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBranch[linhaFromTo]['ANGMIN']),10) +
                str(self.mpcBranch[linhaFromTo]['ANGMAX']) +
                ';\n'
                )
            self.arquivoBranchData += '];\n'

        def escreveArquivoMatPower(self):

            # Se nao existe diretorio para escrever os resultado entao cria
            if not os.path.isdir(DIRETORIO_COM_RESULTADOS_DE_SAIDA): os.makedirs(DIRETORIO_COM_RESULTADOS_DE_SAIDA)

            # /home/francisco/Documents/TCC2/Projeto/Ferramenta-de-conversao/Resultados_Ferramenta_Computacional_ds_ons_122023_rv0d29/ds_ons_122023_rv0d29_Estagio01.m
            caminhoCompletoArquivo = DIRETORIO_COM_RESULTADOS_DE_SAIDA + BLOCO_REVISAO+'_'+self.informacoesEstagio.patamar.split('.')[0]+'.m'

            with open(caminhoCompletoArquivo, 'w') as arquivoMatPower :

                arquivoMatPower.write(self.arquivoCabecalho)
                arquivoMatPower.write(self.arquivobusData)
                arquivoMatPower.write(self.arquivoGeneratorData)
                arquivoMatPower.write(self.arquivoBranchData)
                arquivoMatPower.write(self.arquivoGeneratorCostData)
                arquivoMatPower.write(self.arquivoAdditionalData)

# Funcao responsavel por retornar uma string com n caracteres preenchidos.
# O Objetivo dela consiste em receber um valor, por exemplo 3.61 e concatenar espacos de modo que o resultado seja uma string que totalize a quantidade desejada (tamanhoPreenchimento) 
# O principal objetivo dela eh formatar os espacamentos entre as colunas dos mpc do matpower.
def retornaStringArrumadaParaEscreverComTamanhoCorreto(stringValor, tamanhoPreenchimento):
    # Identifica o tamanho da string recebida pela funcao.
    stringValueLen = len(stringValor)
    # Calcula quantos espacos precisarah inserir para preencher o numero de caracteres requeridos por (tamanhoPreenchimento).
    spaceToFill = tamanhoPreenchimento - stringValueLen

    # Inicializa variavel que irah retornar apos preencher com espacamento a direita, ate atingir tamanhoPreenchimento de caracteres.
    stringValorPreenchida = stringValor
    for i in range (0, spaceToFill):
        # concatena espacos a direita da string recebida na funcao
        stringValorPreenchida += ' '

    return stringValorPreenchida

# Funcao responsavel por corrigir numeracao
def corrigeNumero(stringNumero):
    if stringNumero.startswith('.'):
        # stringNumero = '.1' -> '0.1' 
        stringNumero = '0' + stringNumero
    elif stringNumero.endswith('.'):
        # stringNumero = '1.' -> '1'
        stringNumero = stringNumero[ : len(stringNumero)-1] # remove ultimo caracter
    elif stringNumero.startswith('-.'):
        # stringNumero = '-.1' -> '-0.1'
        stringNumero = '-0' + stringNumero[1:] # substitui '-' por '-0'
    
    return stringNumero