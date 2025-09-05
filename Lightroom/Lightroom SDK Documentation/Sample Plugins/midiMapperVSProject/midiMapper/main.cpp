#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif

#include <Windows.h>
#include <Mmsystem.h>
#include <iostream>
#include <sstream>
#include <WinDef.h>
#include <winsock2.h>
#include <WS2tcpip.h>

#define SENDBYPASS
#define RECEIVEBYPASS

using std::string;

char sendBuff[4];
SOCKET sendSocket;
SOCKET receiveSocket;

bool receiveOnSocket(char * portNo, char * ipAddress)
{
	int iResult;
	struct addrinfo *result = NULL,
					*ptr = NULL,
					hints;
	ZeroMemory(&hints, sizeof(hints));
	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_protocol = IPPROTO_TCP;
	hints.ai_flags = AI_PASSIVE;

	iResult = getaddrinfo(ipAddress, portNo , &hints, &result);

	receiveSocket = INVALID_SOCKET;

	ptr=result;

	receiveSocket = socket(ptr->ai_family, ptr->ai_socktype, ptr->ai_protocol);

	if(receiveSocket == INVALID_SOCKET)
		return false;
	else
	{
		std::cout << "True\n";
	}
	iResult = bind(receiveSocket, ptr->ai_addr, (int)ptr->ai_addrlen);
	if (iResult == SOCKET_ERROR)
	{
		printf("bind failed with error:  %d\n", WSAGetLastError());
		return false;
	}
	else
	{
		std::cout << "True\n";
	}
	SOCKET clientSocket;
	if ( listen( receiveSocket, SOMAXCONN ) == SOCKET_ERROR )
		return false;
	else
	{
		std::cout << "True\n";
	}
	clientSocket = accept(receiveSocket, NULL, NULL);
	if (clientSocket == INVALID_SOCKET)
		return false;
	else
		return true;
	return false;
}

bool sendOnSocket(char * portNo, char * ipAddress)
{
	int iResult;
	struct addrinfo *result = NULL,
					*ptr = NULL,
					hints;
	ZeroMemory(&hints, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_protocol = IPPROTO_TCP;

	iResult = getaddrinfo(ipAddress, portNo , &hints, &result);

	sendSocket = INVALID_SOCKET;

	ptr=result;
	std::cout << "Creating socket\n";
	sendSocket = socket(ptr->ai_family, ptr->ai_socktype, ptr->ai_protocol);

	if(sendSocket == INVALID_SOCKET)
		return false;
	else
	{
		std::cout << "True\n";
	}
	std::cout << "Connecting on socket\n";
	iResult = connect(sendSocket, ptr->ai_addr, (int)ptr->ai_addrlen);
	if (iResult == SOCKET_ERROR)
		return false;
	else
	{
		return true;
		std::cout << "True\n";
	}
	return false;
}

void CloseConnection(SOCKET s)
{
	if(s)
		closesocket(s);
}

void CALLBACK MidiInProc(HMIDIIN hMidiIn, UINT wMsg, DWORD_PTR dwInstance, DWORD_PTR dwParam1, DWORD_PTR dwParam2)
{
	//data 2 | data 1 | status
	//dwParam2 is just the timestamp (in milliseconds)
	sendBuff[2] = (char)((dwParam1 >> 16) & 0xff);
	sendBuff[1] = (char)((dwParam1 >> 8) & 0xff);
	sendBuff[0] = (char)(dwParam1 & 0xff);
	sendBuff[3] = '\n';
	std::cout << sendBuff;
	int iResult = send(sendSocket, sendBuff, 4*sizeof(char), 0);
	std::cout << '\r';
	std::cout << std::hex << ((dwParam1 >> 16) & 0xff) << "\t" << std::hex << ((dwParam1 >> 8) & 0xff) << "\t" << std::hex << (dwParam1 & 0xff);
	if (iResult == SOCKET_ERROR)
		std::cout << "\tSend failed";
	else
		std::cout << "\tSend successful";
}

int main(int argc, char **argv)
{
	WSADATA wsaData;
	if (argv[1] != "midiTest")	//bypass socket setup
	{
		int error = WSAStartup(MAKEWORD(2,2), &wsaData);
		if (error)
			return 1;
		int inPort, outPort;
		string outIpAddress;
		string outPortString;
		string inIpAddress;
		string inPortString;
		#ifdef SENDBYPASS
			std::cout << "Enter IP address (for send): ";
			std::cin >> outIpAddress;
			std::cout << "\nEnter port: ";
			std::cin >> outPortString;
			std::cout << "Connecting to socket on " << outIpAddress << ":" << outPortString << "...";
			if(sendOnSocket(&outPortString[0], &outIpAddress[0]) == true)
			{
				std::cout << "Successful\n";
			}
			else
			{
				std::cout << "Failed\n";
				//return 0;
			}
		#endif
		#ifdef RECEIVEBYPASS
		std::cout << "Enter IP address (for receive): ";
		std::cin >> inIpAddress;
		std::cout << "\nEnter port to receive on: ";
		std::cin >> inPortString;
		std::cout << "Listening on port " << inPortString << "...";
		if(receiveOnSocket(&inPortString[0], &inIpAddress[0]))
		{
			std::cout << "Successful\n";
		}
		else
		{
			std::cout << "Failed...\n";
			//return 0;
		}
		#endif
	}
	UINT numberOfDev = midiInGetNumDevs();
	std::cout << "Number of midi devices: " << numberOfDev << "\n";
	HMIDIIN midiHandle;
	//DWORD_PTR ptr = MidiInProc;
	if (midiInOpen(&midiHandle, 0, (DWORD_PTR) MidiInProc, NULL, CALLBACK_FUNCTION) == MMSYSERR_NOERROR)
	{
		std::cout << "Device was opened!\n";
	}
	if (midiInStart(midiHandle) == MMSYSERR_NOERROR)
	{
		std::cout << "Midi input was started!\n";
	}
	std::cin.get();
	//return 0;
	std::cin.get();
}