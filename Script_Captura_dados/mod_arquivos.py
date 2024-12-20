import sys
from comum_functions import defineEstagio
from comum_functions_base import *
from comum_functions_patamar import *
from comum_functions_usina import *
from comum_functions_cmo import *
from defines import *
import os
from copy import deepcopy

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

            # coletaDadosUsinas nao faz mais sentido, preciso ajustar antes informacoes do dusi, talvez fazer aqui dentro mesmo antes de varrer usinas T e H
            self.informacoesArquivosUsinas = coletaDadosUsinas(USINA_HIDRAULICA, USINA_TERMOELETRICA, USINA_EOLICA, self.estagio)

            self.informacoesCmoBarras = coletaDadosCmoBarras(CMO_BARRAS, self.estagio)
            
            self.montandoEstruturaMpcBus()
            self.montandoEstruturaMpcBranch()
            self.montandoEstruturaMpcGen()
            self.montandoEstruturaMpcBusAdd()
            self.montaArquivoMatPower()
            self.escreveArquivoMatPower()

        def montandoEstruturaMpcBus(self):
            self.mpcBus = {}

            # pegando dados para montar bus_data (mpc.bus)
            for chavebarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase']:
                if self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Estado'] == 'D':
                    # Barras em Estado desligado nao utilizo no mpcGen
                    # A principio barras desligadas nao estao contidas no arquivo pdo_cmo.dat
                    continue

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
                QD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Reativa']
                
                if BUS_I in self.informacoesArquivosUsinas.infoUsinaEolica:
                    try:
                        PD = float(self.informacoesArquivosUsinas.infoUsinaEolica[BUS_I]['Geracao-Operada'])
                        if float(PD) > 0:
                            PD = float(PD) * -1
                        # se ja for menor nao preciso aplicar multiplicacao pra tornar a carga negativa ...
                    except Exception as error:
                        print('problema passando pd para passar para carga negativa, investigue o problema. Barra: '+ BUS_I)
                        print(error)
                        PD = 0
                else:
                    PD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Ativa']
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
                    
                    # Se PD eh proveniente de Eolica nao aplico fator de correcao.
                    if FATOR_CORRECAO_CARGA and BUS_I not in self.informacoesArquivosUsinas.infoUsinaEolica:
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
                    # Para barras sem grupo relacionados no dglt eu seto valores fixos default conforme manual ANAREDE v10.
                    # Formato dos Dados dos Grupos de Limites de Tensão
                    VMAX = '1.2'
                    VMIN = '0.8'

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
                elif STATUS == 'D':
                    # circuito desligado
                    STATUS = '0'

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
            self.mpcGen['H'] = {}
            self.mpcGen['T'] = {}
            self.mpcGen['TOTAL'] = {}
            # TALVEZ AQUI CRIAR um mpcGen['TOTAL'] pra montar arquivo matpower com mais facilidade.

            # MPC GEN GENCOST E GENADD precisam ter mesma estrutura.

            # cada numero de identificacao considero como um gerador, ele sera uma linha de mpc gen por exemplo.
            # posso ter n linhas com a mesma barra, porem sao numeros de identificacao diferente no bloco dusi.
            # no fim das contas mpc gen terah que ter o mesmo numero de numero de identificacao do bloco dusi, sem contar as elevatorias.

            # esse for irah iterar na ordem de coleta do dusi comecando do primeiro elemento. (No 1)
            listaDusiNaoAdicionados = []
            for numeroIdentificacaoDusi in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase']:
                mnemonico           = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][numeroIdentificacaoDusi]['Mnemonico-Identificacao']
                grupo               = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][numeroIdentificacaoDusi]['Numero-Grupo-Pertencimento-Usina']
                unidade             = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][numeroIdentificacaoDusi]['Numero-Unidades-Geradoras-Elemento']
                barra               = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][numeroIdentificacaoDusi]['Numero-Barra-Elemento-Conectado']
                numeroCadastroUsina = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][numeroIdentificacaoDusi]['Numero-Cadastro-Usina']


                if barra not in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase']:
                    listaDusiNaoAdicionados.append(numeroIdentificacaoDusi)
                    continue # nao encontrou a barra e nao adiciono elemento dusi no mpc gen.
                else:


                    BUS_TYPE = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Tipo']
                    if BUS_TYPE == '': BUS_TYPE = '0' # Default
                    # DESSEM PQ = 0, PV = 1, ref V0 = 2
                    # MATPOWER PQ = 1, PV = 2, ref = 3, isolada = 4

                    busConvertionDessemToMatpower = {
                        '0': '1',
                        '1': '2',
                        '2': '3',
                    }
                    BUS_TYPE = busConvertionDessemToMatpower.get(BUS_TYPE, None)

                    if BUS_TYPE == None or BUS_TYPE == '1':
                        listaDusiNaoAdicionados.append(numeroIdentificacaoDusi)
                        continue # barra sem tipo ou barra do tipo PQ, nao inserir no mpc gen e dar um continue na sequencia.

                    GEN_STATUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Estado']
                    # Tratando estado
                    # "L" ou branco => A barra esta ligada;
                    # "D" => A barra esta desligada;
                    GEN_STATUS = '0' if GEN_STATUS == 'D' else '1'

                    # Barras em Estado desligado nao utilizo no mpcGen
                    # A principio barras desligadas nao estao contidas no arquivo pdo_cmo.dat
                    if GEN_STATUS == '0':
                        listaDusiNaoAdicionados.append(numeroIdentificacaoDusi)
                        continue

                    QG   = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Geracao-Reativa']
                    QMAX = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Geracao-Reativa-Maxima']
                    QMIN = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Geracao-Reativa-Minima']
                    VG   = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Tensao']


                    try: VG = str(round((float(VG)/1000),3))
                    except: VG = '0.000'

                    try: QG = str(round(float(QG),2))
                    except: QG = '0.00'

                    try: QMAX = str(round(float(QMAX),2))
                    except: QMAX = '0.00'

                    try: QMIN = str(round(float(QMIN),2))
                    except: QMIN = '0.00'


                    MBASE     = '100' # 100 MVA Arbitrado mas posso pegar no BLOCO DCTE
                    PMIN      = '0.00'
                    PC1       = '0.00'
                    PC2       = '0.00'
                    QC1MIN    = '0.00'
                    QC1MAX    = '0.00'
                    QC2MIN    = '0.00'
                    QC2MAX    = '0.00'
                    RAMP_AGC  = '0.00'
                    RAMP_10   = '0.00'
                    RAMP_30   = '0.00'
                    RAMP_Q    = '0.00'
                    APF       = '0.00'


                    objeto = {
                        'unidade'    : unidade,
                        'gen_unid'   : unidade,
                        'barra'      : barra,
                        'grupo'      : grupo,
                        'mbase'      : MBASE,
                        'pmin'       : PMIN,
                        'pc1'        : PC1,
                        'pc2'        : PC2,
                        'qc1min'     : QC1MIN,
                        'qc1max'     : QC1MAX,
                        'qc2min'     : QC2MIN,
                        'qc2max'     : QC2MAX,
                        'ramp_agc'   : RAMP_AGC,
                        'ramp_10'    : RAMP_10,
                        'ramp_30'    : RAMP_30,
                        'ramp_q'     : RAMP_Q,
                        'apf'        : APF,
                        'qg'         : QG,
                        'vg'         : VG,
                        'qmax'       : QMAX,
                        'qmin'       : QMIN,
                        'gen_status' : GEN_STATUS,
                        'bus_type'   : BUS_TYPE,
                        'gen_id'     : numeroCadastroUsina
                    }

                    # preciso segregar o bloco dusi entre H e T

                    # bloco dusi H
                    # preciso segregar por numero de cadastro da usina, por exemplo:
                    # chave -> numero de cadastro da usina,
                    # valor -> conjunto de dicionarios contendo informacoes pertinentes para cada usina que tenha o mesmo numero de cadastro de usina
                    # Cada numeroIdentificacaoDusi irei considerar como um gerador nas matrizes.
                    # A chave mais externa tem o numero de cadastro porque é mais facil de iterar os arquivos de H e T.

                    # 'H' : {
                    #   'numeroCadastroUsina': {...},
                    #   '173': {
                    #       'numeroIdentificacaoDusi' : {....},
                    #       '4': {'barra': '5030', 'grupo': '1', 'unid': '2',},
                    #       '5': {'barra': '5032', 'grupo': '1', 'unid': '2',},
                    #   }
                    # }


                    # 'T' : {
                    #   'numeroCadastroUsina': {...},
                    #   '201': {
                    #       'numeroIdentificacaoDusi' : {....},
                    #       '232': {'barra': '8646', 'grupo': '1', 'unidade': '3',},
                    #       '233': {'barra': '8646', 'grupo': '1', 'unidade': '4',},
                    #       '234': {'barra': '8653', 'grupo': '1', 'unidade': '1',},
                    #       '235': {'barra': '8653', 'grupo': '1', 'unidade': '2',},
                    #   }
                    # }


                    if mnemonico == 'H':
                        if numeroCadastroUsina not in self.mpcGen['H']:
                            self.mpcGen['H'][numeroCadastroUsina] = {}
                        self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi] = objeto
                    elif mnemonico == 'T':
                        # apenas hidraulica possui grupo, fixo 1 para grupo de termica.
                        objeto['grupo'] = '1'
                        if numeroCadastroUsina not in self.mpcGen['T']:
                            self.mpcGen['T'][numeroCadastroUsina] = {}
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi] = objeto
                    else:
                        # soh uso T e H
                        continue



                    # BLOCO self.mpcGen['T']

                    # 'T' : {
                    #   'numeroCadastroUsina': {...},
                    #   '201': {
                    #       'numeroIdentificacaoDusi' : {....},
                    #       '232': {'barra': '8646', 'grupo': '1', 'unid': '3',},
                    #       '233': {'barra': '8646', 'grupo': '1', 'unid': '4',},
                    #       '234': {'barra': '8653', 'grupo': '1', 'unid': '1',},
                    #       '235': {'barra': '8653', 'grupo': '1', 'unid': '2',},
                    #   }
                    # }

                    # BLOCO self.informacoesArquivosUsinas.infoUsinaTermoeletrica
                    # for usina in self.informacoesArquivosUsinas.infoUsinaTermoeletrica
                            # 201 : {
                            #     1: {...},
                            #     2: {...},
                            #     3: {...},
                            #     4: {...},
                            # },
                            # numeroCadastroUsina : {
                            #     unidade: {...},
                            # }

            # criar um deepcopy para o self.mpcGen
            mpcGen = deepcopy(self.mpcGen)
            # PERCORRER mpcgen mas alterar self.mpcGen.
            dusiRemovidas = {}
            for numeroCadastroUsina in mpcGen['T']:
                for numeroIdentificacaoDusi in mpcGen['T'][numeroCadastroUsina]:
                    unid = mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['unidade']

                    # Se a unidade nao existir no meu bloco de infoUsinaT deleto do meu mpcgen
                    if unid not in self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina]:
                        del self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]
                        dusiRemovidas[numeroIdentificacaoDusi] =  {'TIPO': 'T', 'MOTIVO': 'NAO SE ENCONTRA NO PDO_TERM'}
                        continue

                    try:
                        ESTADO = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Estado']
                    except Exception as error:
                        print('[montandoEstruturaMpcGeneGenaddNova]' + str(error))
                        sys.exit()

                        # TODO: feito
                        # tem dois bloco dusi com numero cadastro 63, unid 1 e 2, e em pdo term soh tem uma unidade, inserir tratativa de 'in' pra nao quebrar
                        # se nao achar no pdo term excluir do bloco self mpc gen.


                    # Coleto a informacao do estado da unidade com base no que armazenei 'L/D'
                    # Se identificar que a unidade para o determinado numero de cadastro de usina ta desligada, removo ela do meu dicionario principal mpcGen
                    if ESTADO == 'D':
                        del self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]
                        dusiRemovidas[numeroIdentificacaoDusi] =  {'TIPO': 'T', 'MOTIVO': 'DESLIGADA'}
                    else:
                        # Coleto informacoes da unidade referente ao numero de cadastro da usina
                        PG       = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Geracao-MW']
                        PMAX     = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Capacidade-MW']
                        PMIN     = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Geracao-Minima-MW']
                        CVU      = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Custo']
                        NOME     = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Usina']
                        SISTEMA  = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[numeroCadastroUsina][unid]['Sistema']

                        try: PG = float(PG)
                        except: PG = 0.00

                        try: PMAX = float(PMAX)
                        except: PMAX = 0.00

                        try: PMIN = float(PMIN)
                        except: PMIN = 0.00

                        # Armazeno as informacoes dentro do meu dicionario principal mpcGen para posterior montagem de MPCGEN GENCOST E GENADD
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['pg']       = str(round(PG,2))
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['pmax']     = str(round(PMAX,2))
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['pmin']     = str(round(PMIN,2))
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['cvu']      = CVU
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['nome']     = NOME
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['sistema']  = SISTEMA
                        self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]['gen_type'] = 'T'

                        self.mpcGen['TOTAL'][numeroIdentificacaoDusi] = self.mpcGen['T'][numeroCadastroUsina][numeroIdentificacaoDusi]

            # vira ->>>>>>
            # Numero de cadastro de usinas vazios significa que todos os numerosdusi todas unidades estavam vazios.
            # Remover numerodecadastro vazios, eles nao irao fazer parte das matrizes finais gen gencost e genadd.
            # {
            #     '1': {},
            #     '13': {
            #         '231': {...}
            #     },
            #     '201': {
            #         '232': {...},
            #         '233': {...},
            #         '234': {...},
            #         '235': {...}
            #     },
            # }

            # Comecar a preencher self.mpcGen['H']
            for numeroCadastroUsina in mpcGen['H']:
                for numeroIdentificacaoDusi in mpcGen['H'][numeroCadastroUsina]:

                    unid = mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['unidade']
                    grupo = mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['grupo']

                    # Se eu nao encontrar o grupo nas informacoes de infoUsinaHidraulica para determinado numero de cadastro de usina,
                    # deleto no info mpc gen H a chave e valor para o numero de identificacao dusi.
                    if not grupo in self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina]:
                        del self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]
                        continue # vai para o proximo numero de identificacao dusi do cadastro da usina.

                    # Verifico o numero de unidades que eu armazenei no infoUsinaHidraulica -> numeroCadastroUsina -> grupo
                    numeroUnidades = len(self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo])
                    # Se nao encontrar unidades deleto tambem no info mpc gen H
                    if numeroUnidades == 0:
                        del self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]
                        continue # vai para o proximo numero de identificacao dusi do cadastro da usina.


                    PG   = 0.00 # concateno
                    PMAX = 0.00
                    PMIN = 0.00
                    CVU  = 0.00
                    NOME  = ''
                    contadorDeUnidades = 0
                    unidadesPercorridas = []
                    unidadesPercorridasDesligadas = []
                    unidadesPercorridasLigadas = []


                    for unidade in  self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo]:
                        # Se meu contador atingir o numero de unidades que tinha que percorrer termino o for.
                        if contadorDeUnidades == unid: break

                        # Marco qual unidade estou percorrendo para deletar depois.
                        unidadesPercorridas.append(unidade)

                        try:
                            ESTADO = self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidade]['Estado']
                        except Exception as error:
                            print('[montandoEstruturaMpcGeneGenaddNova]' + str(error))
                            sys.exit()

                        if ESTADO == 'D':
                            # Se o estado da unidade for desligado eu nao armazeno informacoes.
                            # Ela eh considerada uma unidade percorrida mas registro que ela estava desligada.
                            contadorDeUnidades += 1
                            unidadesPercorridasDesligadas.append(unidade)
                            continue
                        else:
                            # Coleto informacoes da unidade referente ao numero de cadastro da usina e grupo
                            # PG concateno o pg de cada unidade ligada
                            PG   += float(self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidade]['Geracao-MW'])
                            # Sobrescrevo toda vez a cada iteracao o nome mas nao tem problema, todo numero de cadastro mantem o mesmo nome
                            NOME = self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidade]['Usina']
                            # Sobrescrevo toda vez a cada iteracao o sistema mas nao tem problema, todo numero de cadastro mantem o mesmo sistema
                            SISTEMA = self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidade]['Sistema']
                            # PMAX concateno as capacidades
                            PMAX += float(self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidade]['Capacidade-MW'])
                            unidadesPercorridasLigadas.append(unidade)

                        contadorDeUnidades += 1

                    # Se eu identificar que todas unidades que eu passei estavam desligadas, posso deletar minha estrutura dusi.
                    # Se pg igual a 0 porque todas unidades estavam desligadas eu deleto o numero dusi
                    if len(unidadesPercorridas) == len(unidadesPercorridasDesligadas):
                        del self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]
                        continue

                    # Se pg igual a 0 mas os elementos nao estavam desligadas eu nao deleto o numero dusi.
                    # Se todos elementos foram zero ja deletei o elemento dusi.
                    # Aqui so insiro o PG.
                    # Pendente inserir outros dados..
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['pg']        = str(round(PG,2))
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['pmax']      = str(round(PMAX,2))
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['pmin']      = str(round(PMIN,2))
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['cvu']       = str(CVU)
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['nome']      = NOME
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['sistema']   = SISTEMA
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['gen_unid']  = ','.join(unidadesPercorridasLigadas)
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['gen_id']    = numeroCadastroUsina
                    self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]['gen_type']  = 'H'

                    self.mpcGen['TOTAL'][numeroIdentificacaoDusi] = self.mpcGen['H'][numeroCadastroUsina][numeroIdentificacaoDusi]
                    # Zero novamente o contador de unidades
                    contadorDeUnidades = 0
                    # Agora eu removo as unidades percorridas para na proxima iteracao elas nao estarem presente novamente.
                    for unidadeDeletar in unidadesPercorridas:
                        del self.informacoesArquivosUsinas.infoUsinaHidraulica[numeroCadastroUsina][grupo][unidadeDeletar]


                        # info mpc gen H
                        # 'H' : {
                        #   'numeroCadastroUsina': {...},
                        #   '174': {
                        #       'numeroIdentificacaoDusi' : {....},
                        #       '217': {'barra': '6555', 'grupo': '1', 'unid': '3',},
                        #       '218': {'barra': '6556', 'grupo': '2', 'unid': '1',},
                        #       '219': {'barra': '6559', 'grupo': '2', 'unid': '1',},
                        #       '220': {'barra': '6559', 'grupo': '3', 'unid': '1',},
                        #       '221': {'barra': '6559', 'grupo': '4', 'unid': '1',},
                        #       '222': {'barra': '6559', 'grupo': '4', 'unid': '1',},
                        #       '223': {'barra': '6559', 'grupo': '4', 'unid': '1',},
                        #       '224': {'barra': '6559', 'grupo': '5', 'unid': '2',},
                        #       '225': {'barra': '6559', 'grupo': '5', 'unid': '2',},                                   
                        #   }
                        # }


                        # info usina HIDR pdo_h
                        # numeroCadastroUsina -> grupo -> unidade
                        # 174 : {
                        #     1: {
                        #       1: {...},
                        #       2: {...},
                        #       3: {...},
                        #     },
                        #     2: {
                        #       1: {...},
                        #       2: {...},
                        #     },
                        #     3: {
                        #       1: {...},
                        #     },
                        #     4: {
                        #       1: {...},
                        #       2: {...},
                        #       3: {...},
                        #     },
                        #     5: {
                        #       1: {...},
                        #       2: {...},
                        #       3: {...},
                        #       4: {...},
                        #     },
                        #     99: {
                        #       99: {...},
                        #     },                               
                        # }

        # MpcGen poderia ser aproveitado para montar MpcBusAdd uma vez que ele realiza os mesmos lacos por dbar.
        # Aproveitar MpcGen seria uma esforco computacional menor, como o algoritmo nao precisa ficar atendendo solicitacoes em tempo real nao vejo motivos para nao organizar outro bloco de construcao da estrutura busadd.
        def montandoEstruturaMpcBusAdd(self):
            self.mpcBusAdd = {}
            for barra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase']:
                if self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Estado'] == 'D':
                    # Barras em Estado desligado nao utilizo no mpcGen nem aqui em mpcBusAdd
                    # A principio barras desligadas nao estao contidas no arquivo pdo_cmo.dat
                    continue

                BUS_NAME = ''
                BUS_SUBS = ''
                BUS_CMO = ''
                NOME_USINA_CORRETO = ''
                GEN_TYPE = ''
                
                # numero da barra, 260 por exemplo.
                GEN_BUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][barra]['Numero']

                if GEN_BUS in self.informacoesCmoBarras.infoCmo:
                    if 'Nome-Barra' in self.informacoesCmoBarras.infoCmo[GEN_BUS] and \
                       'Subsistema' in self.informacoesCmoBarras.infoCmo[GEN_BUS] and \
                       'Custo-Marginal' in self.informacoesCmoBarras.infoCmo[GEN_BUS]:
                        BUS_NAME = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Nome-Barra']
                        BUS_SUBS = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Subsistema']
                        BUS_CMO = self.informacoesCmoBarras.infoCmo[GEN_BUS]['Custo-Marginal']
                    else:
                        BUS_NAME = '-'
                        BUS_SUBS = '-'
                        BUS_CMO = '0.00'
                else:
                        BUS_NAME = '-'
                        BUS_SUBS = '-'
                        BUS_CMO = '0.00'

                try: float(BUS_CMO)
                except: BUS_CMO = '0.00'

                # preciso pegar gen_type e gen_name
                # verificar inicialmente se a barra ta no dusi, se tiver pego tipo e procuro nos resultados de T e H
                # se ela nao estiver tento ver se esta nos resultados de Eolica.


                # varrendo
                # self.mpcGen['H']
                EncontreiGEN_BUS = False
                if not EncontreiGEN_BUS:
                    for numeroCadastroUsina in self.mpcGen['H']:
                        for NumeroIdentificacaoDusi in self.mpcGen['H'][numeroCadastroUsina]:
                            if GEN_BUS == self.mpcGen['H'][numeroCadastroUsina][NumeroIdentificacaoDusi]['barra']:
                                NOME_USINA_CORRETO = self.mpcGen['H'][numeroCadastroUsina][NumeroIdentificacaoDusi]['nome']
                                GEN_TYPE = self.mpcGen['H'][numeroCadastroUsina][NumeroIdentificacaoDusi]['gen_type'] # 'H'
                                EncontreiGEN_BUS = True
                #varrendo
                # self.mpcGen['T']
                if not EncontreiGEN_BUS:
                    for numeroCadastroUsina in self.mpcGen['T']:
                        for NumeroIdentificacaoDusi in self.mpcGen['T'][numeroCadastroUsina]:
                            if GEN_BUS == self.mpcGen['T'][numeroCadastroUsina][NumeroIdentificacaoDusi]['barra']:
                                NOME_USINA_CORRETO = self.mpcGen['T'][numeroCadastroUsina][NumeroIdentificacaoDusi]['nome']
                                GEN_TYPE = self.mpcGen['T'][numeroCadastroUsina][NumeroIdentificacaoDusi]['gen_type'] # 'T'
                                EncontreiGEN_BUS = True


                if not EncontreiGEN_BUS:
                    if GEN_BUS in self.informacoesArquivosUsinas.infoUsinaEolica:
                        GEN_TYPE = self.informacoesArquivosUsinas.infoUsinaEolica[GEN_BUS]['Tipo'] # fixado em EO
                        NOME_USINA_CORRETO = self.informacoesArquivosUsinas.infoUsinaEolica[GEN_BUS]['Nome']
                        ncontreiGEN_BUS = True



                if not GEN_TYPE: GEN_TYPE = '-'
                if not NOME_USINA_CORRETO: NOME_USINA_CORRETO = '-'

                # barra = '10', '50'....
                self.mpcBusAdd[barra] = {
                'BUS_I'   : GEN_BUS,
                'BUS_NAME': BUS_NAME,
                'BUS_SUBS': BUS_SUBS,
                'BUS_CMO' : str(BUS_CMO),
                'GEN_TYPE': GEN_TYPE,
                'GEN_NAME': NOME_USINA_CORRETO,
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

            self.GeneratorAdditionalData = ''
            self.GeneratorAdditionalData += '%% generator additional data\n'
            # self.GeneratorAdditionalData += '%	bus_i	gen_name	gen_type	gen_unid	gen_group	gen_id
            self.GeneratorAdditionalData += ('%	' + 	retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_i',16) +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_name',16)       +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_type',16)       +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_id',16)         +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_group',16)      +
            'gen_unid'      +
            '\n')
            self.GeneratorAdditionalData += 'mpc.genadd = [\n'

            self.arquivoGeneratorCostData = ''
            self.arquivoGeneratorCostData += '%%----- OPF Data -----%%\n'
            self.arquivoGeneratorCostData += '%% generator cost data\n'
            self.arquivoGeneratorCostData += '%	1	startup	shutdown	n	x1	y1	...	xn	yn\n'
            self.arquivoGeneratorCostData += '%	2	startup	shutdown	n	c(n-1)	...	c0\n'
            self.arquivoGeneratorCostData += 'mpc.gencost = [\n'


            self.arquivoAdditionalData = ''
            self.arquivoAdditionalData += '%% bus additional data\n'
            self.arquivoAdditionalData += ('%	'+retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_i',16)   +
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_name',16)                                      + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_subs',16)                                      + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('bus_cmo',16)                                       + # pegar do CMO
            retornaStringArrumadaParaEscreverComTamanhoCorreto('gen_type',16)                                      +
            'gen_name\n'
            )
            self.arquivoAdditionalData += 'mpc.busadd = {\n'

            for numeroDusi in self.mpcGen['TOTAL']:

                # mpcgen
                self.arquivoGeneratorData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['barra']),10)                     +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['pg'])),10)         +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['qg'])),10)         +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['qmax'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['qmin'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['vg']),10)                        +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['mbase']),10)                     +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['gen_status']),10)                +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['pmax'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(corrigeNumero(str(self.mpcGen['TOTAL'][numeroDusi]['pmin'])),10)       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['pc1']),10)                       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['pc2']),10)                       +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['qc1min']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['qc1max']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['qc2min']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['qc2max']),10)                    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['ramp_agc']),10)                  +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['ramp_10']),10)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['ramp_30']),10)                   +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['ramp_q']),10)                    +
                    str(self.mpcGen['TOTAL'][numeroDusi]['apf'])  +
                    ';\n'
                    )
                
                # mpcgencost
                self.arquivoGeneratorCostData += (
                    doisTabEspace + 
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('2',10)                                          +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('0',10)                                          +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('0',10)                                          +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto('2',10)                                          +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['cvu']),10) +
                    '0' +
                    ';\n'
                    )
                
                # mpcgen
                self.GeneratorAdditionalData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['barra']),16)             +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(repr(str(self.mpcGen['TOTAL'][numeroDusi]['nome'])),16)        +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(repr(str(self.mpcGen['TOTAL'][numeroDusi]['gen_type'])),16)    +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcGen['TOTAL'][numeroDusi]['gen_id']),16)            +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto((str(self.mpcGen['TOTAL'][numeroDusi]['grupo'])),16)           +
                    repr(str(self.mpcGen['TOTAL'][numeroDusi]['gen_unid']))  +
                    ';\n'
                    )


            for chavebarra in self.mpcBusAdd:
                # mpcbusadd
                self.arquivoAdditionalData += (
                    doisTabEspace +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBusAdd[chavebarra]['BUS_I']),16)        +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(repr(str(self.mpcBusAdd[chavebarra]['BUS_NAME'])),16) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(repr(str(self.mpcBusAdd[chavebarra]['BUS_SUBS'])),16) +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(str(self.mpcBusAdd[chavebarra]['BUS_CMO']),16)        +
                    retornaStringArrumadaParaEscreverComTamanhoCorreto(repr(str(self.mpcBusAdd[chavebarra]['GEN_TYPE'])),16)     +
                    repr(str(self.mpcBusAdd[chavebarra]['GEN_NAME']))                                                      +
                    ';\n'
                    )

            self.arquivoGeneratorData += '];\n'
            self.arquivoGeneratorData += '%\n'

            self.arquivoGeneratorCostData += '];\n'
            self.arquivoGeneratorCostData += '%\n'

            self.GeneratorAdditionalData += '];\n'
            self.GeneratorAdditionalData += '%\n'

            self.arquivoAdditionalData += '};\n'
            self.arquivoAdditionalData += '%\n'

            self.arquivoBranchData = ''
            self.arquivoBranchData += '%% branch data\n'
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
                arquivoMatPower.write(self.GeneratorAdditionalData)
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