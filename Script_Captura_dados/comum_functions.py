import sys

# Com base no minuto e hora informado seleciona o estagio para passar para o infoCasoBase
# Soh aceita fracoes de meia hora para minuto, como por exemplo minuto: '00' ou '30'
# Soh aceita hora de 00 a 23, sendo a primeira hora 00:00 estagio 1 e ultima hora 23:00 estagio 47
def defineEstagio(hora, minuto):
    estagios  = retornaEstagios()

    timeEstagio = hora+':'+minuto
    estagio = estagios.get(timeEstagio, None)

    if estagio: return estagio
    raise Exception('Nao conseguiu encontrar o estagio para a hora e minuto determinado')

def retornaEstagios():
    estagios = {
        '00:00' : '01',
        '00:30' : '02',
        '01:00' : '03',
        '01:30' : '04',
        '02:00' : '05',
        '02:30' : '06',
        '03:00' : '07',
        '03:30' : '08',
        '04:00' : '09',
        '04:30' : '10',
        '05:00' : '11',
        '05:30' : '12',
        '06:00' : '13',
        '06:30' : '14',
        '07:00' : '15',
        '07:30' : '16',
        '08:00' : '17',
        '08:30' : '18',
        '09:00' : '19',
        '09:30' : '20',
        '10:00' : '21',
        '10:30' : '22',
        '11:00' : '23',
        '11:30' : '24',
        '12:00' : '25',
        '12:30' : '26',
        '13:00' : '27',
        '13:30' : '28',
        '14:00' : '29',
        '14:30' : '30',
        '15:00' : '31',
        '15:30' : '32',
        '16:00' : '33',
        '16:30' : '34',
        '17:00' : '35',
        '17:30' : '36',
        '18:00' : '37',
        '18:30' : '38',
        '19:00' : '39',
        '19:30' : '40',
        '20:00' : '41',
        '20:30' : '42',
        '21:00' : '43',
        '21:30' : '44',
        '22:00' : '45',
        '22:30' : '46',
        '23:00' : '47',
        '23:30' : '48',
    }
    return estagios

# dicionario = {'1' : 'a', '2': 'b'}
# retorno = {'a': '1', 'b': '2'}
def retornaDicionarioInvertido(dicionario):
    NovoDicionario = {}
    for key, value in dicionario.items(): NovoDicionario[value] = key
    return NovoDicionario

# Recebe dois array do mesmo tamanho, ordena o arrB em ordem crescente e pivoteia arrD conforme ordena arrB.
# Ex entradas: arrB = [8,2,2,6,4,5], arrD = ['1','2','3','4','5','6'] -> arrB precisa ser uma lista de <int>, arrD pode ser qualquer tipo.
# ex saidas:   arrB = [2,2,4,5,6,8], arrD = ['2','3','5','6','4','1']
def bubble_sort(arrB, arrD):
    if len(arrB) != len(arrD): sys.exit('[bubble_sort] Erro, arrB e arrD devem ter mesmo tamanho.')

    n = len(arrB)
    for i in range(n - 1):
        for j in range(n - 1 - i): # - i porque a cada termino de iteracao aqui, garanto que o maior numero foi para a ultima posicao do array
            if arrB[j] > arrB[j+1]:

                arrB[j], arrB[j+1] = arrB[j+1], arrB[j] # troca (atual) pelo (proximo) e (proximo) pelo (atual). array de inteiros que queremos ordenar
                arrD[j], arrD[j+1] = arrD[j+1], arrD[j] # troca (atual) pelo (proximo) e (proximo) pelo (atual). array de inteiros ou str que deve seguir pivoteamento de arrB
    return arrB, arrD


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