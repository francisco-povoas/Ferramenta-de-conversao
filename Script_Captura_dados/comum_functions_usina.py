import sys

# Coleta informacoes dentro do array com as informacoes da linha da usina Hidraulica.
# Ex linearray: ['  1 ', '   LEVE ', '  1 ', ' CAMARGOS     ', ' SE ', '  99 ', '   99  ', '      0.00 ', '    264.24 ', '     39.32 ', '     67.00 ', '      0.12 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.00 ', '      0.08 ', '      0.00 ', '      0.20  ', '      0.00  ', '    181.43 ', '      0.33 ', '      0.00 ', '      0.00 ', '    205.75 ', '      0.37 ', '    205.75 ', '      0.37 ', '    778.59 ', '      1.40 ', '     28.49 ', '      46.00 ', '      46.00 ', '  -  ', '      0.00 ', '     20.21 ']
def getusinaHInformacoesDalinha(linearray):
    try:
        hidroInfoLine = {
            'Estagio': linearray[0].strip(),
            'Patamar': linearray[1].strip(),
            'Numero-Cadastro-Usina': linearray[2].strip(),
            'Usina': linearray[3].strip(),
            'Sistema': linearray[4].strip(),
            'Conj': linearray[5].strip(),
            'Unid': linearray[6].strip(),
            'Vagua-MWh': linearray[7].strip(),
            'Geracao-MW':linearray[32].strip(),
            'Geracao-Maxima-MW':linearray[33].strip(),
            'Geracao-Minima-MW': '0.00', # Valor arbitrado, Nao possui informacao no arquivo
            'Capacidade-MW':linearray[34].strip(),
            'Estado':linearray[35].strip(),
            'Tipo': 'H',
        }
    except Exception as error:
        print(error)
        return None, error
    return hidroInfoLine, None

# Coleta informacoes dentro do array com as informacoes da linha da usina Termoeletrica.
# Ex linearray: ['  1 ', '  LEVE ', '  1 ', 'ANGRA 1      ', '  1 ', ' SE ', '      0.00 ', '      0.00 ', '      0.00 ', '     640.00 ', '  D  ', '     31.17 ']
def getusinaTInformacoesDalinha(linearray):
    try:
        termoInfoLine = {
            'Estagio': linearray[0].strip(),
            'Patamar': linearray[1].strip(),
            'Numero-Cadastro-Usina': linearray[2].strip(),
            'Usina': linearray[3].strip(),
            'Unid': linearray[4].strip(),
            'Sistema': linearray[5].strip(),
            'Geracao-MW':linearray[6].strip(),
            'Geracao-Minima-MW': linearray[7].strip(),
            'Geracao-Maxima-MW':linearray[8].strip(),
            'Capacidade-MW':linearray[9].strip(),
            'Estado':linearray[10].strip(),
            'Custo':linearray[11].strip(),
            'Tipo': 'T',
        }
    except Exception as error:
        print(error)
        return None, error
    return termoInfoLine, None

# Coleta informacoes dentro do array com as informacoes da linha da usina Eolica.
# Ex linearray: ['   1 ', '     1 ', ' 5G260  _MMGD ', '   260   ', ' SE      ', '     9999.0 ', '      1.000 ', '        0.0 ', '        0.0      ']
def getusinaEInformacoesDalinha(linearray):
    try:
        eolicaInfoLine = {
            'Estagio': linearray[0].strip(),
            'Numero': linearray[1].strip(),
            'Nome': linearray[2].strip(),
            'Barra': linearray[3].strip(),
            'Subsistema': linearray[4].strip(),
            'Geracao-Operada': linearray[8].strip(),
            'Tipo': 'EO', # diferenciando de 'E' -> Elevatoria do bloco dusi
        }
    except Exception as error:
        print(error)
        return None, error
    
    return eolicaInfoLine, None

# Responsavel por coletar informacoes referente a geracao das Usinas Hidraulicas para determinado estagio
class coletaDadosUsinas:
    def __init__(self, arquivoUsinaHidraulica, arquivoUsinaTermoeletrica, arquivoUsinaEolica, estagio):
        self.estagio = int(estagio)

        self.arquivoUsinaHidraulica = arquivoUsinaHidraulica
        self.arquivoUsinaTermoeletrica = arquivoUsinaTermoeletrica
        self.arquivoUsinaEolica = arquivoUsinaEolica

        self.varreArquivoUsinaHidraulica()
        self.varreArquivoUsinaTermoeletrica()
        self.varreArquivoUsinaEolica()

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

                        # Ex usinaInfoHidraulicaLine = {'Estagio': '1', 'Patamar': 'LEVE', 'Numero-Cadastro-Usina': '260', 'Usina': 'PIMENTAL', 'Sistema': 'N', 'Geracao-MW': '79.34', 'Geracao-Maxima-MW': '233.10', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '233.10'}, 'FOZ R. CLARO': {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'FOZ R. CLARO', 'Sistema': 'SE', 'Geracao-MW': '6.92', 'Geracao-Maxima-MW': '34.20', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '68.40'}}
                        usinaInfoHidraulicaLine, error = getusinaHInformacoesDalinha(infoLineArray)
                        if error: sys.exit()

                        numeroCadastroUsina = usinaInfoHidraulicaLine['Numero-Cadastro-Usina']
                        unidade = usinaInfoHidraulicaLine['Unid']
                        grupo = usinaInfoHidraulicaLine['Conj']

                        #     usina = usinaInfoHidraulicaLine['Usina']
                        #     usinaInfoHidraulica[usina] = usinaInfoHidraulicaLine

                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   1 ;    1  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     40.00 ;     -      ;      40.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   1 ;    2  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     40.00 ;     -      ;      40.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   2 ;    1  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     45.45 ;     -      ;      48.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   2 ;    2  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;      0.00 ;     -      ;      48.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   3 ;    1  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     49.00 ;     -      ;      49.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   3 ;    2  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     49.00 ;     -      ;      49.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   3 ;    3  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     49.00 ;     -      ;      49.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   3 ;    4  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     49.00 ;     -      ;      49.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   4 ;    1  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;     41.52 ;     -      ;      52.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;   4 ;    2  ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;           ;            ;            ;           ;           ;           ;           ;   1272.00 ;      2.29 ;           ;           ;           ;           ;      0.00 ;     -      ;      52.00 ;  L  ;      0.00 ;           ;
                        #   1 ;   LEVE ;  7 ; M. DE MORAES ; SE ;  99 ;   99  ;      0.00 ;   1895.19 ;     75.81 ;     78.00 ;      0.14 ;      0.00 ;      0.00 ;    776.00 ;      1.40 ;      0.00 ;      0.00 ;      0.45 ;      0.00 ;      0.60  ;      0.00  ;   1166.44 ;      2.10 ;      0.00 ;      0.00 ;   1170.10 ;      2.11 ;   1170.10 ;      2.11 ;   3192.86 ;      5.75 ;    362.97 ;     476.00 ;     476.00 ;  -  ;      0.00 ;     36.57 ;

                        # 7 : {
                        #     1: {
                        #       1: {...},
                        #       2: {...},
                        #     },
                        #     2: {
                        #       1: {...},
                        #       2: {...},
                        #     },
                        #     3: {
                        #       1: {...},
                        #       2: {...},
                        #       3: {...},
                        #       4: {...},
                        #     },
                        #     4: {
                        #       1: {...},
                        #       2: {...},
                        #     },
                        #     99: {
                        #       99: {...},
                        #     },
                        # }

                        if numeroCadastroUsina not in usinaInfoHidraulica:
                            usinaInfoHidraulica[numeroCadastroUsina] = {}

                        if grupo not in usinaInfoHidraulica[numeroCadastroUsina]:
                            usinaInfoHidraulica[numeroCadastroUsina][grupo] = {}

                        usinaInfoHidraulica[numeroCadastroUsina][grupo][unidade] = usinaInfoHidraulicaLine


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
            # Abrindo arquivo relacionado ao estagio, ex: 'pdo_term.dat', 
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

                        # despreza linha com valor 99
                        if '99' in infoLineArray[4]:
                            continue

    
                        # Ex usinaInfoHidraulicaLine = {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'PIMENTAL', 'Sistema': 'N', 'Geracao-MW': '79.34', 'Geracao-Maxima-MW': '233.10', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '233.10'}, 'FOZ R. CLARO': {'Estagio': '1', 'Patamar': 'LEVE', 'Usina': 'FOZ R. CLARO', 'Sistema': 'SE', 'Geracao-MW': '6.92', 'Geracao-Maxima-MW': '34.20', 'Geracao-Minima-MW': '0.00', 'Capacidade-MW': '68.40'}}
                        usinaInfoTermoeletricaLine, error = getusinaTInformacoesDalinha(infoLineArray)
                        if error: sys.exit()

                        # usinaInfoTermoeletricaLine['Custo-Linear-MWh'] = custoLinear

                        # estado = usinaInfoTermoeletricaLine['Estado']
                        # so quero unidades Ligadas
                        # if estado != 'L': continue

                        numeroCadastroUsina = usinaInfoTermoeletricaLine['Numero-Cadastro-Usina']
                        unidade = usinaInfoTermoeletricaLine['Unid']


                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  4 ; NE ;      0.00 ;      0.00 ;     69.44 ;      69.44 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  5 ; NE ;      0.00 ;      0.00 ;     69.44 ;      69.44 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  6 ; NE ;      0.00 ;      0.00 ;     69.44 ;      69.44 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  7 ; NE ;      0.00 ;      0.00 ;    114.08 ;     114.08 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  8 ; NE ;      0.00 ;      0.00 ;    114.08 ;     114.08 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ;  9 ; NE ;      0.00 ;      0.00 ;    104.16 ;     104.16 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ; 10 ; NE ;      0.00 ;      0.00 ;    114.08 ;     114.08 ;  L  ;   1244.94 ;
                        # 1 ;  LEVE ; 55 ;GLOBAL II    ; 11 ; NE ;

                        # 55 : {
                        #     1: {...},
                        #     2: {...},
                        #     3: {...},
                        #     4: {...},
                        #     5: {...},
                        #     6: {...},
                        #     7: {...},
                        #     8: {...},
                        #     9: {...},
                        #     10: {...},
                        #     11: {...},
                        # },
                        # numeroCadastroUsina : {
                        #     unidade: {...}
                        # }


                        if numeroCadastroUsina not in usinaInfoTermoeletrica:
                            usinaInfoTermoeletrica[numeroCadastroUsina] = {}

                        usinaInfoTermoeletrica[numeroCadastroUsina][unidade] = usinaInfoTermoeletricaLine

                        # salvamento antigo
                        # salvo a chave como o numero de cadastro com a unidade.
                        # usinaInfoTermoeletrica[numeroCadastroUsina+'-'+unidade] = usinaInfoTermoeletricaLine

                if periodo > self.estagio:
                    break        
                
        except Exception as error:
            print(error)
            sys.exit()
        self.infoUsinaTermoeletrica = usinaInfoTermoeletrica

    def varreArquivoUsinaEolica(self):
        try:
            # Abrindo arquivo relacionado ao estagio, ex: 'pdo_eolica.dat', 
            with open(self.arquivoUsinaEolica,'r', encoding='latin-1') as arquivo:
                self.arquivoUsinaEolicaLido = arquivo.readlines()

            periodo = False
            usinaInfoEolica = {}

            # Varrendo arquivo
            for line in self.arquivoUsinaEolicaLido:
            
                if 'IPER ;' in line: # Encontrou bloco IPER
                    periodo = True
                    continue
                
                if periodo and (line.startswith('  -  ;') or line.startswith('-----;')) :
                    # Pulando duas linhas imediatamente apos IPER
                    continue
                
                if periodo:
                    periodo = int(line[0:4].strip())

                    if periodo == self.estagio:
                        
                        infoLineArray = str(line).split(';')
                        infoLineArray.pop() # remove ultimo indice nao aproveitavel


                        # Ex usinaInfoEolicaLine = {'Estagio': '1', 'Numero': '1', 'Nome': '5G260  _MMGD', 'Barra': '260', 'Subsistema': 'SE', 'Geracao-Operada': '0.0'}
                        usinaInfoEolicaLine, error = getusinaEInformacoesDalinha(infoLineArray)
                        if error: sys.exit()

                        # pegando numero da barra, '322' por exemplo.
                        barra = usinaInfoEolicaLine['Barra']

                        # No arquivo pdo_eolica.dat a geracao operada pode estar em mais de uma linha, conforme exemplo do arquivo para barra 222:
                        # -----;-------;--------------;---------;---------;------------;------------;------------;-----------------;
                        # IPER ;  NUM  ;     Nome     ;  Barra  ; Submerc ;  Potencia  ;   FatCap   ;  Geracao   ; Geracao Operada ;
                        #   -  ;   -   ;      -       ;    -    ;    -    ;     -      ;     -      ;     -      ;        -        ;
                        # -----;-------;--------------;---------;---------;------------;------------;------------;-----------------;
                        # ....
                        # ....
                        # 1 ;    44 ; A2COCF _CORU ;   322   ; SE      ;     9999.0 ;      1.000 ;       20.0 ;       20.0      ;
                        # 1 ;    45 ; A5CRDO _Cerr ;   322   ; SE      ;     9999.0 ;      1.000 ;       25.0 ;       25.0      ;

                        # usinaInfoEolica armazenarah apenas uma chave para cada barra.
                        # se a barra em questao nao estiver ainda no usinaInfoEolica armazeno todas as informacoes.
                        # se a barra jah estiver no usinaInfoEolica eu pego a geracao que esta em Geracao-Operada e transformo em float somando com o novo valor encontrado.
                        # Note que a mesma barra 322 pode ter dois nomes para o numero 44 e 45. Diferente da Geracao operada que somamos, o Nome eu concateno com um pipe |


                        if barra in usinaInfoEolica:
                            nomeAtualizado = usinaInfoEolica[barra]['Nome'] + ' | ' + usinaInfoEolicaLine['Nome']
                            usinaInfoEolica[barra]['Nome'] = nomeAtualizado
                            
                            try:
                                geracaoOperadaGuardada = float(usinaInfoEolica[barra]['Geracao-Operada'])
                                geracaoOperadaAtual = float(usinaInfoEolicaLine['Geracao-Operada'])

                                # tentando atualizar a geracao-operada com o que ja haviamos guardado com a nova captura de valor.
                                usinaInfoEolica[barra]['Geracao-Operada'] = str(geracaoOperadaGuardada + geracaoOperadaAtual)


                            except Exception as error:
                                print('Investique o problema, nao foi possivel atualizar o valor da Geracao Operada para a barra: ' + barra)
                                print(error)
                            
                            # so atualiza geracao-operada e nome, nao crio nova chave em usinaInfoEolica, ela ja existe, entao continue.
                            continue
                        
                        # so cria novas chaves, quando a barra ja foi adicionada anteriormente, so atualiza nome e geracao operada...
                        usinaInfoEolica[barra] = usinaInfoEolicaLine

                if periodo > self.estagio:
                    break        
                
        except Exception as error:
            print(error)
            sys.exit()
        self.infoUsinaEolica = usinaInfoEolica
