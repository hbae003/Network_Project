import socket
import sys
import random
from thread import *

HOST = '10.0.0.4'
PORT = 4090

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket Created'

try:
	s.bind((HOST, PORT))
except socket.error , msg:
	print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
	sys.exit()

print 'Socket bind complete'

s.listen(10)
print 'Socket now listening'

def find(s, ch):
	return [i for i, Itr in enumerate(s) if Itr == ch]


#game class 
class Game:
	#constructor
	def __init__(self, diff, word, conn):
		self.difficulty = diff
		self.word = word
		self.output = "_" * len(word)
		self.wrongList = []
		self.connectedList = []		#(conn, username, score)
		self.playerTurn = conn

	#mutators
	def connect(self, conn, user):
		self.connectedList.append((conn, user, 0))
	
	def disconnect(self, conn, user, score):
		self.connectedList.remove((conn, user, score))

	def guessChar(self, guess):	#takes in a char and returns a hit or miss (true/false)
		indexes = find(self.word, guess)
		if not indexes:		#empty list (miss)
			self.wrongList.append(guess)
			self.wrongList.append(' ')
			return 0
		else:			#hit
			outputList = list(self.output)
			for i in indexes:
				outputList[i] = guess
			self.output = "".join(outputList)
			return len(indexes)

	def guessWord(self, guess):
		if guess == self.word:
			self.output = self.word
			return True
		return False		
	
	def nextTurn(self):
		temp = [y[0] for y in self.connectedList]
		current_index = temp.index(self.playerTurn)
		current_index = current_index + 1 
		if current_index != len(self.connectedList):
			self.playerTurn = temp[current_index]
		else:	
			self.playerTurn = temp[0]
	
	def updateScore(self, user, score):
		for i,e  in enumerate(self.connectedList):
			if e[1] == user:
				temp = list(self.connectedList[i])
				temp[2] = score
				self.connectedList[i] = tuple(temp)		

	#accessors 
	def out(self):
		temp = [x[0] for x in self.connectedList]
		for conn in temp:
			conn.send(self.output + '\n')
			conn.send('Wrong Characters so far: ')
			conn.send("".join(self.wrongList) + '\n')
			for x,y,z in self.connectedList:
				conn.send(y + ' ' + str(z))
				if x == self.playerTurn:
					conn.send('*\n')
				else:
					conn.send('\n')

	def get_playerTurn(self):
		return self.playerTurn
	
	def get_word_length(self):
		return len(self.word)
	
	def get_conn(self):
		return self.connectedList

	def end_game_check(self):
		if self.output == self.word:
			return True
		if self.difficulty == 1:
			if len(self.wrongList)/2 >= 3 * len(self.word):
				return True
		if self.difficulty == 2:
			if len(self.wrongList)/2 >= 2 * len(self.word):
				return True
		if self.difficulty == 3:
			if len(self.wrongList)/2 >= len(self.word):
				return True
		return False

	def end_game_output(self):
		temp = [x[0] for x in self.connectedList]
		for conn in temp:
			conn.send('GAME ENDED\nFINAL SCORES:\n')
			for x,y,z in self.connectedList:
				conn.send(y + ' ' + str(z) + '\n')

#global variables
gameNum = 0
wordList = ['kylekuzma', 'lonzoball', 'sportcraft', 'brandoningram', 'nowayyoucanguessthis']
uList = ['user', 'peter']
loggedList = []
upList = [('user','pass'), ('peter', 'bae')]
clientList = []
topScores = []
gameList = []

#Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
	#define global variables 
	global gameNum
	global wordList
	global uList
	global upList
	global clientList
	global topScores
	global gameList

	#variables for each client
	curr_state = 'init'
	client_game_connect = 0		#the client will use this variable to know which game its playing
	game_playing = None
	client_score = 0
	username = ""

	#infinite loop so that function do not terminate and thread do not end
	while True:
		#main menu page
		if curr_state == 'init':
			conn.send('\n1.Login\n2.Make New user\n3.Hall of Fame\n4.Exit\n\n')
			data = conn.recv(1024)
			data = data.rstrip()
			#user login
			if data == '1':
				conn.send('Username: ')
				rcv_user = conn.recv(1024)
				rcv_user = rcv_user.rstrip()
				conn.send('Password: ')
				rcv_pass = conn.recv(1024)
				rcv_pass = rcv_pass.rstrip()
				if (rcv_user,rcv_pass) in upList:
					curr_state = 'logged'
					username = rcv_user
					loggedList.append(username)
				else:
					conn.send('Username and Password does not exist')
			#make new user
			if data == '2':
				conn.send('Username: ')
				rcv_user = conn.recv(1024)
				rcv_user = rcv_user.rstrip()
				if rcv_user in uList:
					conn.send('Username already exists')
				else:
					uList.append(rcv_user)
					conn.send('Password: ')
					rcv_pass = conn.recv(1024)
					rcv_pass = rcv_pass.rstrip()
					upList.append((rcv_user,rcv_pass))
			#hall of fame
			if data == '3':
				if not topScores:
					conn.send('Hall of Fame is currently empty\n')
				else:
					conn.send('Hall of Fame:\n')
					for a,b in topScores:
						reply =  a + ' ' + str(b) + '\n'
						conn.sendall(reply)
			#log user out
			if data == '4':
				conn.send('Logging off\n')
				clientList.remove(conn)
				loggedList.remove(username)
				break
		#user has logged in
		if curr_state == 'logged':
			conn.send('\n1.Start New Game\n2.Get list of the Games\n3.Hall of Fame\n4.Exit\n\n')
			data = conn.recv(1024)
			data = data.rstrip()
			#start new game
			if data == '1':
				curr_state = 'level'
			#get list of games
			if data == '2':
				curr_state = 'choose_game'
			#hall of fame
			if data == '3':
				if not topScores:
					conn.send('Hall of Fame is currently empty\n')
				else:
					conn.send('Hall of Fame:\n')
					for a,b in topScores:
						reply =  a + ' ' + str(b) + '\n'
						conn.sendall(reply)
			#log user out
			if data == '4':
				conn.send('Logging off\n')
				clientList.remove(conn)
				loggedList.remove(username)
				break
		if curr_state == 'choose_game':
			conn.send('List of Games:\n')
			for x,y in gameList:
				conn.send('Game number ' + str(y) + '\n')
			conn.send('Enter q to go back\n')
			data = conn.recv(1024)
			data = data.rstrip()
			if data != 'q':
				client_game_connect = int(data)
				curr_state = 'connect_client_to_game'
			else:
				curr_state = 'logged'
					
	
		#user is choosing the level
		if curr_state == 'level':
			conn.send('\nChoose the difficulty\n1.Easy\n2.Medium\n3.Hard\n\n')
			data = conn.recv(1024)
			data = data.rstrip()
			if data == '1':	
				temp_game = Game(1, random.choice(wordList), conn)
				gameList.append((temp_game, gameNum))
				client_game_connect = gameNum
				gameNum = gameNum + 1
				curr_state = 'connect_client_to_game'
			elif data == '2':
				temp_game = Game(2, random.choice(wordList), conn)
				gameList.append((temp_game, gameNum))
				client_game_connect = gameNum
				gameNum = gameNum + 1
				curr_state = 'connect_client_to_game'
			elif data == '3':
				temp_game = Game(3, random.choice(wordList), conn)
				gameList.append((temp_game, gameNum))
				client_game_connect = gameNum
				gameNum = gameNum + 1
				curr_state = 'connect_client_to_game'
		
		#connecting user to game
		if curr_state == 'connect_client_to_game':
			#find the game the client will play
			for a,b in gameList:
				if client_game_connect == b:
					game_playing = a
			game_playing.connect(conn, username)
			curr_state = 'game'
			

		#user is playing game
		if curr_state == 'game':
			game_end_flag = False
			if game_playing.get_playerTurn() != conn:
				conn.send('Waiting for turn...\n')
				while game_playing.get_playerTurn() != conn and game_end_flag == False:
					if game_playing.end_game_check():
						game_end_flag = True	#game ended 
						curr_state = 'reset_variables'
					pass #do nothing
			#only enter if the game is still running
			if game_end_flag == False:
				game_playing.out()
				conn.send('Enter a guess: ')
				data = conn.recv(1024)
				data = data.rstrip()
				#user only entered one char
				if len(data) == 1:
					temp_guess = game_playing.guessChar(data)
					if temp_guess > 0:
						client_score = client_score + temp_guess
						game_playing.updateScore(username, client_score)
					else:
						game_playing.nextTurn()
				#user entered a word
				else:
					if game_playing.guessWord(data):
						client_score = client_score + game_playing.get_word_length()
						game_playing.updateScore(username, client_score)
					else:
						game_playing.nextTurn()
						curr_state = 'incorrect_guess'
				#check that the game did not end
				if game_playing.end_game_check():
					game_playing.end_game_output()
					gameList = [i for i in gameList if i[0] != game_playing]
					curr_state = 'reset_variables'

		#reset variables and add/sort top scores
		if curr_state == 'reset_variables':
			topScores.append((username, client_score))
			topScores = sorted(topScores, key=lambda x: x[1], reverse=True)
			client_score = 0
			game_playing = None
			curr_state = 'logged'
		
		#the user guessed incorrectly and is booted from game
		if curr_state == 'incorrect_guess':
			game_playing.disconnect(conn, username, client_score)
			client_score = 0
			curr_state = 'logged'
			
	conn.close()

def serverthread(input, input2):
	while 1:
		print '\n1.Current list of users\n2.Current list of the words\n3.Add new word to the list of words\n'
		admin_input = raw_input('Choose from options: ')
		if admin_input == '1':
			print '\nList of users logged in:'
			if len(loggedList) > 0:
				for x in loggedList:
					print x
			else:
				print 'No users are logged in'
			print 'List of users saved into server:'
			for x in uList:
				print x
		if admin_input == '2':
			print '\nList of words:'
			for x in wordList:
				print x
		if admin_input == '3':
			admin_input = raw_input('Enter word to add: ') 
			wordList.append(admin_input)
			


#start server thread
start_new_thread(serverthread, (1,1))	
#now keep talking with the client
while 1:
	#wait to accept a connection - blocking call
	conn, addr = s.accept()
	clientList.append(conn)

	#start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function
	start_new_thread(clientthread , (conn,addr))

s.close()
