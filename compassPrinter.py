from sense_hat import SenseHat
sense = SenseHat()
sense.set_rotation(0)
while(True):
    print(str(sense.get_compass()))
