import sys
from comum_functions import defineEstagio
from comum_functions_base import *
from comum_functions_patamar import *
from comum_functions_usina import *
from defines import *

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
            self.arquivoPatamar  = CAMINHO + self.informacoesEstagio.arquivoPatamar # Ex .: Diretorio/pat01.afp
            
            self.informacoesBlocosArquivoBase = coletaBlocosArquivoBase(self.arquivoCasoBase)

            self.informacoesBlocosArquivoPatamar = coletaBlocosArquivosPatamar(self.arquivoPatamar)

            self.informacoesArquivosUsinas = coletaDadosUsinas(USINA_HIDRAULICA, USINA_TERMOELETRICA, self.estagio)
            
            self.montandoEstruturaMpcBus()
            self.montandoEstruturaMpcBranch()
            self.montandoEstruturaMpcGen()
            self.montaArquivoMatPower()
            self.escreveArquivoMatPower()

            self.montaArquivoMatPower()

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

                # if (BUS_TYPE != '0' and BUS_TYPE != '1' and BUS_TYPE != '2' and BUS_TYPE != ''):
                #     print('BUS_TYPE='+ BUS_TYPE)

                BUS_AREA = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Area']
                PD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Ativa']
                QD = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Carga-Reativa']
                if PD == '': PD = '0'
                if QD == '': QD = '0'
                
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


                Grupo_De_Base_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-De-Base-De-Tensao'] # usado apenas para pegar a tensao base no bloco dgbt
                if Grupo_De_Base_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase']:
                    BASEKV = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase'][Grupo_De_Base_De_Tensao]['Tensao-Nominal-Grupo-Base-KV']

                VM = (float(VM)/float(BASEKV))

                self.mpcBus[BUS_I] = {
                    'BUS_I': BUS_I,
                    'BUS_TYPE': BUS_TYPE,
                    'PD': str(PD),
                    'QD': str(QD),
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
                ANGMAX = '+360'

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
                
                # Tentando converter para PU 
                try:
                    BR_R = str(round(float(BR_R)/100),5)
                except:
                    pass
                
                try:
                    BR_X = str(round(float(BR_X)/100),5)
                except:
                    pass

                try:
                    BR_B = str(round(float(BR_B)/100),5)
                except:
                    pass

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

                GEN_BUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Numero']
                PG = ''
                QG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa']
                QMAX = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Maxima']
                QMIN = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Minima']
                VG = ''
                MBASE = 100 # 100 MVA Arbitrado mas posso pegar no BLOCO DCTE
                GEN_STATUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Estado']
                PMAX = ''
                PMIN = '0.00'
                PC1 = '0.00'
                PC2 = '0.00'
                QC1MIN = '0.00'
                QC1MAX = '0.00'
                QC2MIN = '0.00'
                QC2MAX = '0.00'
                RAMP_AGC = '0.00'
                RAMP_10 = '0.00'
                RAMP_30 = '0.00'
                RAMP_Q = '0.00'
                APF = '0.00'

                # Tratando estado
                # "L" ou branco => A barra está ligada;
                # "D" => A barra está desligada;
                GEN_STATUS = '0' if GEN_STATUS == 'D' else '1'

                VG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Tensao'] # Preciso dividir pelo Tensao-Nominal-Grupo-Base-KV do bloco DGBT
                
                Grupo_De_Base_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-De-Base-De-Tensao'] # usado apenas para pegar a tensao base no bloco dgbt
                if Grupo_De_Base_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase']:
                    BASEKV = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase'][Grupo_De_Base_De_Tensao]['Tensao-Nominal-Grupo-Base-KV']

                VG = (float(VG)/float(BASEKV))

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

                NOME_USINA = ''
                for chaveNumeroBarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase']:
                    two = 0
                    if(chaveNumeroBarra == GEN_BUS):
                        
                        NOME_USINA = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][chaveNumeroBarra]['Nome-Usina']

                        for usina in self.informacoesArquivosUsinas.infoUsinaHidraulica:
                            if(usina == NOME_USINA):
                                two += 1
                                geracaoUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-MW']
                                geracaoMaximaUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-Maxima-MW']
                                geracaoMinimaUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-Minima-MW']
                                custoUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Vagua-MWh']
                                TIPO = 'H'

                        for usina in self.informacoesArquivosUsinas.infoUsinaTermoeletrica:
                            if(usina == NOME_USINA):
                                two += 1
                                geracaoUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-MW']
                                geracaoMaximaUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-Maxima-MW']
                                geracaoMinimaUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-Minima-MW']
                                custoUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Custo-Linear-MWh']
                                TIPO = 'T'

                # Defendendo contra erro e somando potencias na barra
                try: geracaoUsinaHidraulica = float(geracaoUsinaHidraulica)
                except: geracaoUsinaHidraulica == 0.00

                try: geracaoUsinaTermoeletrica = float(geracaoUsinaTermoeletrica)
                except: geracaoUsinaTermoeletrica == 0.00

                PG = geracaoUsinaHidraulica +  geracaoUsinaTermoeletrica 

                # Defendendo contra erro e somando geração maxima (Potencia max) na barra
                try: geracaoMaximaUsinaHidraulica = float(geracaoMaximaUsinaHidraulica)
                except: geracaoMaximaUsinaHidraulica = 0.00

                try: geracaoMaximaUsinaTermoeletrica = float(geracaoMaximaUsinaTermoeletrica)
                except: geracaoMaximaUsinaTermoeletrica = 0.00

                PMAX = geracaoMaximaUsinaHidraulica + geracaoMaximaUsinaTermoeletrica

                # Defendendo contra erro e somando geração minima (Potencia min) na barra
                try: geracaoMinimaUsinaHidraulica = float(geracaoMinimaUsinaHidraulica)
                except: geracaoMinimaUsinaHidraulica = 0.00

                try: geracaoMinimaUsinaTermoeletrica = float(geracaoMinimaUsinaTermoeletrica)
                except: geracaoMinimaUsinaHidraulica = 0.00

                PMIN = geracaoMinimaUsinaHidraulica + geracaoMinimaUsinaTermoeletrica

                try: custoUsinaHidraulica = float(custoUsinaHidraulica)
                except: custoUsinaHidraulica = 0.00

                try: custoUsinaTermoeletrica = float(custoUsinaTermoeletrica)

                except: custoUsinaTermoeletrica = 0.00

                CVU = custoUsinaHidraulica + custoUsinaTermoeletrica

                # chavebarra = 'barra-10', 'barra-50'....
                self.mpcGen[chavebarra] = {
                'GEN_BUS': GEN_BUS,
                'PG': PG,
                'QG': QG,
                'QMAX': QMAX,
                'QMIN': QMIN,
                'VG': VG,
                'MBASE': MBASE,
                'GEN_STATUS': GEN_STATUS,
                'PMAX': PMAX,
                'PMIN': PMIN,
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
                'TIPO': TIPO, # Usado no mpc genname
                'NOME_USINA': NOME_USINA,
                }
                # f.write(str(self.mpcGen[chavebarra]['GEN_BUS']) +' '+str(+self.mpcGen[chavebarra]['CVU'])+'\n' )
                
        def montaArquivoMatPower(self):

            self.arquivoCabecalho = ''
            self.arquivoCabecalho += 'function mpc = '+self.informacoesEstagio.patamar+'\n'
            self.arquivoCabecalho += '% CASO SIN: extraido dos arquivos de dados do DESSEM\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '% CASO SIN: Fluxo de Potencia do SIN extraido de arquivo de dados do DESSEM\n'
            self.arquivoCabecalho += '% Autor Francisco Povoas\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%   MATPOWER\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%% MATPOWER Case Format : Version 2\n'
            self.arquivoCabecalho += 'mpc.version = \'2\';\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%%-----  Power Flow Data  -----%%\n'
            self.arquivoCabecalho += '%\n'
            self.arquivoCabecalho += '%% system MVA base\n'
            self.arquivoCabecalho += 'mpc.baseMVA = 100;\n'

            self.arquivoCabecalho += '%\n'
            self.arquivobusData = ''
            self.arquivobusData += '%% bus data\n'
            self.arquivobusData += '%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin\n'
            self.arquivobusData += 'mpc.bus = [\n'

            for BUS in self.mpcBus:
                self.arquivobusData += (
                    '    ' + str(self.mpcBus[BUS]['BUS_I']) + '       ' +
                    str(self.mpcBus[BUS]['BUS_TYPE']) + '       ' +
                    str(self.mpcBus[BUS]['PD']) + '   ' +
                    str(self.mpcBus[BUS]['QD']) + '   ' +
                    str(self.mpcBus[BUS]['GS']) + '   ' +
                    str(self.mpcBus[BUS]['BS']) + '     ' +
                    str(self.mpcBus[BUS]['AREA']) + '     ' +
                    str(self.mpcBus[BUS]['VM']) + '   ' +
                    str(self.mpcBus[BUS]['VA']) + '   ' +
                    str(self.mpcBus[BUS]['BASEKV']) + '     ' +
                    str(self.mpcBus[BUS]['ZONE']) + '     ' +
                    str(self.mpcBus[BUS]['VMAX']) + '     ' +
                    str(self.mpcBus[BUS]['VMIN']) + ';\n'
                    )

            self.arquivobusData += '    ];\n'
            self.arquivobusData += '%\n'

            self.arquivoGeneratorData = ''
            self.arquivoGeneratorData += '%% generator data\n'
            self.arquivoGeneratorData += '%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf\n'
            self.arquivoGeneratorData += 'mpc.gen = [\n'
            
            self.arquivoGeneratorCostData = ''
            self.arquivoGeneratorCostData += '%%----- OPF Data -----%%\n'
            self.arquivoGeneratorCostData += '%% generator cost data\n'
            self.arquivoGeneratorCostData += '%	1	startup	shutdown	n	x1	y1	...	xn	yn\n'
            self.arquivoGeneratorCostData += '%	2	startup	shutdown	n	c(n-1)	...	c0\n'
            self.arquivoGeneratorCostData += 'mpc.gencost = [\n'


            self.arquivoGeneratorName = ''
            self.arquivoGeneratorName += '%% generator name\n'
            self.arquivoGeneratorName += '%	bus	tipo name\n'
            self.arquivoGeneratorName += 'mpc.genname = [\n'

            for chavebarra in self.mpcGen:

                # mpcgen
                self.arquivoGeneratorData += (
                    '    ' +str(self.mpcGen[chavebarra]['GEN_BUS']) + ' ' +
                    str(self.mpcGen[chavebarra]['PG']) + ' ' +
                    str(self.mpcGen[chavebarra]['QG']) + ' ' +
                    str(self.mpcGen[chavebarra]['QMAX']) + ' ' +
                    str(self.mpcGen[chavebarra]['QMIN']) + ' ' +
                    str(self.mpcGen[chavebarra]['VG']) + ' ' +
                    str(self.mpcGen[chavebarra]['MBASE']) + ' ' +
                    str(self.mpcGen[chavebarra]['GEN_STATUS']) + ' ' +
                    str(self.mpcGen[chavebarra]['PMAX']) + ' ' +
                    str(self.mpcGen[chavebarra]['PMIN']) + ' ' +
                    str(self.mpcGen[chavebarra]['PC1']) + ' ' +
                    str(self.mpcGen[chavebarra]['PC2']) + ' ' +
                    str(self.mpcGen[chavebarra]['QC1MIN']) + ' ' +
                    str(self.mpcGen[chavebarra]['QC1MAX']) + ' ' +
                    str(self.mpcGen[chavebarra]['QC2MIN']) + ' ' +
                    str(self.mpcGen[chavebarra]['QC2MAX']) + ' ' +
                    str(self.mpcGen[chavebarra]['RAMP_AGC']) + ' ' +
                    str(self.mpcGen[chavebarra]['RAMP_10']) + ' ' +
                    str(self.mpcGen[chavebarra]['RAMP_30']) + ' ' +
                    str(self.mpcGen[chavebarra]['RAMP_Q']) + ' ' +
                    str(self.mpcGen[chavebarra]['APF']) + ';\n'
                    )
                
                # mpcgencost
                self.arquivoGeneratorCostData += (
                    '2' + ' ' +
                    '0' + ' ' +
                    '0' + ' ' +
                    '2' + ' ' +
                    str(self.mpcGen[chavebarra]['CVU']) + ' ' +
                    '0' + ';\n'
                    )
                
                # mpcgenname
                self.arquivoGeneratorName += (
                    str(self.mpcGen[chavebarra]['GEN_BUS']) + ' ' +
                    str(self.mpcGen[chavebarra]['TIPO']) + ' ' +
                    str(self.mpcGen[chavebarra]['NOME_USINA']) + ';\n'
                    )

            self.arquivoGeneratorData += '    ];\n'
            self.arquivoGeneratorData += '%\n'

            self.arquivoGeneratorCostData += '    ];\n'
            self.arquivoGeneratorCostData += '%\n'

            self.arquivoBranchData = ''
            self.arquivoBranchData += '%% branch data\n'
            self.arquivoBranchData += '%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax\n'
            self.arquivoBranchData += 'mpc.branch = [\n'
            for linhaFromTo in self.mpcBranch:
                self.arquivoBranchData += (
                '    ' + str(self.mpcBranch[linhaFromTo]['F_BUS']) + '         ' +
                str(self.mpcBranch[linhaFromTo]['T_BUS']) + '         ' +
                str(self.mpcBranch[linhaFromTo]['BR_R']) + '         ' +
                str(self.mpcBranch[linhaFromTo]['BR_X']) + '         ' +
                str(self.mpcBranch[linhaFromTo]['BR_B']) + '         ' +
                str(self.mpcBranch[linhaFromTo]['RATE_A']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['RATE_B']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['RATE_C']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['RATIO']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['ANGLE']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['STATUS']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['ANGMIN']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['ANGMAX']) + ';\n'
            )
            self.arquivoBranchData += '];\n'

        def escreveArquivoMatPower(self):

            # ds_ons_122023_rv0d29+'_'+'pat01'+'.m'
            # 'ds_ons_122023_rv0d29_pat01.m'
            with open(BLOCO_REVISAO+'_'+self.informacoesEstagio.patamar.split('.')[0]+'.m', 'w') as arquivoMatPower:

                arquivoMatPower.write(self.arquivoCabecalho)
                arquivoMatPower.write(self.arquivobusData)
                arquivoMatPower.write(self.arquivoGeneratorData)
                arquivoMatPower.write(self.arquivoBranchData)
                arquivoMatPower.write(self.arquivoGeneratorCostData)
                arquivoMatPower.write(self.arquivoGeneratorName)
