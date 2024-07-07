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

            self.montaArquivoMatCad()

        def montandoEstruturaMpcBus(self):
            self.mpcBus = {}
            # cont = 1

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
                RATIO = '0'
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
                    BR_R = str(float(BR_R)/100)
                except:
                    pass
                
                try:
                    BR_X = str(float(BR_X)/100)
                except:
                    pass

                try:
                    BR_B = str(float(BR_B)/100)
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
                PG = '' # OK
                QG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa']
                QMAX = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Maxima']
                QMIN = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Geracao-Reativa-Minima']
                VG = '' # OK
                MBASE = 100 # 100 MVA Arbitrado mas posso pegar no BLOCO DCTE
                GEN_STATUS = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Estado']
                PMAX = ''
                PMIN = 0.00 # valor arbitrado
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
                # "L" ou branco => A barra está ligada;
                # "D" => A barra está desligada;
                GEN_STATUS = '0' if GEN_STATUS == 'D' else '1'

                # Duvida o VG eh igual ao VM do mpcbus, qual a diferenca! por enquanto vou usar o mesmo...
                VG = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Tensao'] # Preciso dividir pelo Tensao-Nominal-Grupo-Base-KV do bloco DGBT
                
                Grupo_De_Base_De_Tensao = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dbarInfoBase'][chavebarra]['Grupo-De-Base-De-Tensao'] # usado apenas para pegar a tensao base no bloco dgbt
                if Grupo_De_Base_De_Tensao in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase']:
                    BASEKV = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dgbtInfoBase'][Grupo_De_Base_De_Tensao]['Tensao-Nominal-Grupo-Base-KV']

                VG = (float(VG)/float(BASEKV))

                # declarando antes do laco for as variaveis de geracao caso nao entre no if que elas sao usadas
                geracaoUsinaHidraulica = 0.00
                geracaoUsinaTermoeletrica = 0.00
                geracaoMaximaUsinaHidraulica = 0.00
                geracaoMaximaUsinaTermoeletrica = 0.00
                nomeUsina = ''
                for chaveNumeroBarra in self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase']:
                    if(chaveNumeroBarra == GEN_BUS):
                        
                        nomeUsina = self.informacoesBlocosArquivoBase.respCompletaBlocosInfoBase['dusiInfoBase'][chaveNumeroBarra]['Nome-Usina']

                        for usina in self.informacoesArquivosUsinas.infoUsinaHidraulica:
                            if(usina == nomeUsina):
                                geracaoUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-MW']
                                geracaoMaximaUsinaHidraulica = self.informacoesArquivosUsinas.infoUsinaHidraulica[usina]['Geracao-Maxima-MW']

                        for usina in self.informacoesArquivosUsinas.infoUsinaTermoeletrica:
                            if(usina == nomeUsina):
                                geracaoUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-MW']
                                geracaoMaximaUsinaTermoeletrica = self.informacoesArquivosUsinas.infoUsinaTermoeletrica[usina]['Geracao-Maxima-MW']
                
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

                # if PMAX != 0.0:
                #     print(PMAX)

                # if PG != 0.0:
                #     print(PG)

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
                }


        def montaArquivoMatCad(self):

            arquivo = ''
            arquivo += 'function mpc = '+self.informacoesEstagio.patamar+'\n'
            arquivo += '% CASO SIN: extraido dos arquivos de dados do DESSEM\n'
            arquivo += '%\n'
            arquivo += '% CASO SIN: Fluxo de Potencia do SIN extraido de arquivo de dados do DESSEM\n'
            arquivo += '% Autor Francisco Povoas\n'
            arquivo += '%\n'
            arquivo += '%   MATPOWER\n'
            arquivo += '%\n'
            arquivo += '%% MATPOWER Case Format : Version 2\n'
            arquivo += 'mpc.version = \'2\';\n'
            arquivo += '%\n'
            arquivo += '%%-----  Power Flow Data  -----%%\n'
            arquivo += '%\n'
            arquivo += '%% system MVA base\n'
            arquivo += 'mpc.baseMVA = 100;\n'
            arquivo += '%\n'
            arquivo += '%% bus data\n'
            arquivo += '%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin\n'
            arquivo += 'mpc.bus = [\n'

            for BUS in self.mpcBus:
                # arquivo += '    '+self.mpcBus[BUS]['BUS_I']+'       '+self.mpcBus[BUS]['BUS_TYPE']+'       '+self.mpcBus[BUS]['PD']+'   '+self.mpcBus[BUS]['QD']+'   '+self.mpcBus[BUS]['GS']+'   '+self.mpcBus[BUS]['BS']+'     '+self.mpcBus[BUS]['AREA']+'     '+self.mpcBus[BUS]['VM']+'   '+self.mpcBus[BUS]['VA']+'   '+self.mpcBus[BUS]['BASEKV']+'     '+self.mpcBus[BUS]['ZONE']+'     '+self.mpcBus[BUS]['VMAX']+'     '+self.mpcBus[BUS]['VMIN']+';\n'
                arquivo += (
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

            arquivo += '    ];\n'
            arquivo += '%\n'
            arquivo += '%% generator data\n'
            arquivo += '%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf\n'
            arquivo += 'mpc.gen = [\n'
            
            for chavebarra in self.mpcGen:
                # print(self.mpcGen[chavebarra])
                # arquivo += +self.mpcGen[chavebarra]['GEN_BUS']+' '+self.mpcGen[chavebarra]['PG']+' '+self.mpcGen[chavebarra]['QG']+' '+self.mpcGen[chavebarra]['QMAX']+' '+self.mpcGen[chavebarra]['QMIN']+' '+self.mpcGen[chavebarra]['VG']+' '+self.mpcGen[chavebarra]['MBASE']+' '+self.mpcGen[chavebarra]['GEN_STATUS']+' '+self.mpcGen[chavebarra]['PMAX']+' '+self.mpcGen[chavebarra]['PMIN']+' '+self.mpcGen[chavebarra]['PC1']+' '+self.mpcGen[chavebarra]['PC2']+' '+self.mpcGen[chavebarra]['QC1MIN']+' '+self.mpcGen[chavebarra]['QC1MAX']+' '+self.mpcGen[chavebarra]['QC2MIN']+' '+self.mpcGen[chavebarra]['QC2MAX']+' '+self.mpcGen[chavebarra]['RAMP_AGC']+' '+self.mpcGen[chavebarra]['RAMP_10']+' '+self.mpcGen[chavebarra]['RAMP_30']+' '+self.mpcGen[chavebarra]['RAMP_Q']+' '+self.mpcGen[chavebarra]['APF']+';\n'
                arquivo += (
                    str(self.mpcGen[chavebarra]['GEN_BUS']) + ' ' +
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
            
            arquivo += '    ];\n'
            arquivo += '%\n'
            arquivo += '%% branch data\n'
            arquivo += '%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax\n'
            arquivo += 'mpc.branch = [\n'
            for linhaFromTo in self.mpcBranch:
                # arquivo += '    '+self.mpcBranch[linhaFromTo]['F_BUS']+'     '+self.mpcBranch[linhaFromTo]['T_BUS']+self.mpcBranch[linhaFromTo]['BR_R']+self.mpcBranch[linhaFromTo]['BR_X']+self.mpcBranch[linhaFromTo]['BR_B']+self.mpcBranch[linhaFromTo]['RATE_A']+self.mpcBranch[linhaFromTo]['RATE_B']+self.mpcBranch[linhaFromTo]['RATE_C']+self.mpcBranch[linhaFromTo]['RATIO']+self.mpcBranch[linhaFromTo]['ANGLE']+self.mpcBranch[linhaFromTo]['STATUS']+self.mpcBranch[linhaFromTo]['ANGMIN']+self.mpcBranch[linhaFromTo]['ANGMAX']+';\n'
                arquivo += (
                '    ' + str(self.mpcBranch[linhaFromTo]['F_BUS']) + '     ' +
                str(self.mpcBranch[linhaFromTo]['T_BUS']) +
                str(self.mpcBranch[linhaFromTo]['BR_R']) +
                str(self.mpcBranch[linhaFromTo]['BR_X']) +
                str(self.mpcBranch[linhaFromTo]['BR_B']) +
                str(self.mpcBranch[linhaFromTo]['RATE_A']) +
                str(self.mpcBranch[linhaFromTo]['RATE_B']) +
                str(self.mpcBranch[linhaFromTo]['RATE_C']) +
                str(self.mpcBranch[linhaFromTo]['RATIO']) +
                str(self.mpcBranch[linhaFromTo]['ANGLE']) +
                str(self.mpcBranch[linhaFromTo]['STATUS']) +
                str(self.mpcBranch[linhaFromTo]['ANGMIN']) +
                str(self.mpcBranch[linhaFromTo]['ANGMAX']) + ';\n'
            )
            arquivo += '];\n'
