from mod_arquivos import tratamentoGeralArquivos
import sys
from comum_functions import retornaEstagios, retornaDicionarioInvertido

if __name__ == "__main__":

    print('Qual procedimento voce gostaria de seguir? Gerar arquivo matpower para um estagio especifico ou gerar os 48 estagios?\n')
    print('(1) para estagio especifico\n(2) para gerar para os 48 estagios de 00h:00m ate 23h:30m\n')
    escolha = str(input('Entre com sua opcao:\n'))

    if escolha == '1':
        print('Opcao 1 escolhida, sera gerado um arquivo .m para um estagio especifico\n')
        print('Horario entre 00:00 e 23:30')
        hora = str(input('Informe a hora, respeitando as seguintes entradas: 00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23\nHora desejada: '))
        minutos = str(input('Informe os minutos, respeitando as seguintes entradas: 00, 30\nMinuto desejado: '))
        try:
            horaAvaliacao = int(hora)
            minutosAvaliacao = int(minutos)

            if (horaAvaliacao < 0 or horaAvaliacao > 23):
                raise Exception('Hora informada incorretamente, leia novamente as entradas permitidas para opcao 2.')

            if (minutosAvaliacao != 0 and minutosAvaliacao != 30):
                raise Exception('Minutos informado incorretamente, leia novamente atentamente as entradas permitidas para opcao 2.')

        except Exception as error:
            print(error)
            sys.exit(1)

        objetoContendoInformacoesGerais = tratamentoGeralArquivos(hora, minutos)
        print('Finalizado, confira na pasta de resultados')
    elif escolha == '2':
        print('Opcao 2 escolhida, sera gerado um arquivo .m para cada um dos estagios\nIsso pode levar um tempo, aguarde ate a finalizacao.')
        estagios = retornaEstagios()
        estagios = retornaDicionarioInvertido(estagios)

        for estagio in range (1,49):
            estagio = str(estagio).zfill(2)
            horaMinuto = estagios.get(estagio, None)
            if horaMinuto == None:
                print('Problema para determinar hora e minuto do estagio')
                sys.exit(1)

            if not ':' in horaMinuto:
                print('Problema com a formatacao da hora minuto, esperava uma separacao por :')
                sys.exit(1)

            lHoraMinutos = horaMinuto.split(':')
            hora = lHoraMinutos[0]
            minutos = lHoraMinutos[1]
            try:
                horaAvaliacao = int(hora)
                minutosAvaliacao = int(minutos)
                if (horaAvaliacao < 0 or horaAvaliacao > 23):
                    raise Exception('Hora informada incorretamente, leia novamente as entradas permitidas para opcao 2.')

                if (minutosAvaliacao != 0 and minutosAvaliacao != 30):
                    raise Exception('Minutos informado incorretamente, leia novamente atentamente as entradas permitidas para opcao 2.')

            except Exception as error:
                print(error)
                sys.exit(1)
            
            print('Gerando arquivo para o estagio '+ str(estagio)+'...')
            objetoContendoInformacoesGerais = tratamentoGeralArquivos(hora, minutos)
        print('Finalizado, confira na pasta de resultados')
    else:
        print('Opcao desconhecida, tente novamente...')
        sys.exit(1)