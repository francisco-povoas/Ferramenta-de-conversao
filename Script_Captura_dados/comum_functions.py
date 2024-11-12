
# Com base no minuto e hora informado seleciona o estagio para passar para o infoCasoBase
# Soh aceita fracoes de meia hora para minuto, como por exemplo minuto: '00' ou '30'
# Soh aceita hora de 00 a 23, sendo a primeira hora 00:00 estagio 1 e ultima hora 23:00 estagio 47
def defineEstagio(hora, minuto):
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
    timeEstagio = hora+':'+minuto
    estagio = estagios.get(timeEstagio, None)

    if estagio: return estagio
    raise Exception('Nao conseguiu encontrar o estagio para a hora e minuto determinado')


