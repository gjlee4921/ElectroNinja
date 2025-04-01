# electroninja/llm/prompts/button_prompts.py


COMPILE_CODE_DESC_PROMPT = (
    "You are a world-class electrical engineer with absolute authority in circuit interpretation.\n"
    "You will recieve a circuit image and you have to describe the circuit in detail.\n"
    "IMPORTANT: You must list all the components in the circuit and their values, as well as their configuration (series / parallel or a combination of the two).\n"
    "Be extra careful with whether the components are in series or parallel, as this is very important. Usually components in series are mostly horizontal while those in parallel are mostly vertical.\n"
    "In AC batteries, the voltage after 'AC' is the amplitude. If before the 'AC' there is one number, this is the DC offset. If there are 3 numbers, the 1st one is the DC offset and the last one is the frequency\n"
    "For the rest of the components, their values are shown close to them\n"
    "Your answer should always come after a 'DESC='\n"
    "For example, if you see a circuit with a DC battery 5V and 2 resistors in parallel 2 and 3 ohms, you should answer with: \n"
    "DESC=A circuit with a 5V DC battery, a 2-ohm resistor and a 3-ohm resistor in parallel.\n"
    "Now do the description as described above, and do not add any other information.\n\n"
)

COMPILE_CODE_COMP_PROMPT = (
    "You are a world-class electrical engineer with absolute authority in reviewing .asc code.\n"
    "You will recieve some .asc code and you have to list all the components in there.\n"
    "There are 4 possible coponents that if identified in the code they must be listed:\n"
    "1. Resistor (R), in .asc code if there are resistors present you will see a 'res'\n"
    "2. Capacitor (C), in .asc code if there are capacitors present you will see a 'cap'\n"
    "3. Inductor (L), in .asc code if there are inductors present you will see a 'ind'\n"
    "4. Diode (D), in .asc code if there are diodes present you will see a 'diode'\n"
    "Your answer should ONLY be one or more capital letters representing the components present in the code.\n"
    "If you see resistirs add an 'R', if you see capacitors add a 'C', if you see inductors add a 'L' and if you see diodes add a 'D'.\n"
    "We do not care about the order of the letters, and neither we do about the quantity of the components from a letter, it will still only be one.\n"
    "For example, if the code is the following:\n"
    """Version 4
    SHEET 1 880 680
    WIRE 192 128 96 128
    WIRE 304 128 272 128
    WIRE 432 128 384 128
    WIRE 96 160 96 128
    WIRE 96 256 96 240
    WIRE 496 256 496 128
    WIRE 496 256 96 256
    WIRE 96 288 96 256
    FLAG 96 288 0
    SYMBOL voltage 96 144 R0
    WINDOW 123 0 0 Left 0
    WINDOW 39 0 0 Left 0
    SYMATTR InstName V1
    SYMATTR Value SINE(0 AC 1)
    SYMBOL res 288 112 R90
    WINDOW 0 0 56 VBottom 2
    WINDOW 3 32 56 VTop 2
    SYMATTR InstName R1
    SYMATTR Value 100
    SYMBOL cap 496 112 R90
    WINDOW 0 0 32 VBottom 2
    WINDOW 3 32 32 VTop 2
    SYMATTR InstName C1
    SYMATTR Value 0.1e-6
    SYMBOL ind 400 112 R90
    WINDOW 0 5 56 VBottom 2
    WINDOW 3 32 56 VTop 2
    SYMATTR InstName L1
    SYMATTR Value 0.01
    """
    "Your answer should be: 'R,C,L' (ONLY the letters)\n"

    "Now list the components for the following code as described above, and do not add any other information.\n\n"

    "{asc_code}\n\n"

)