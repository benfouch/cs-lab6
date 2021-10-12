"""
- NOTE: REPLACE 'N' Below with your section, year, and lab number
- CS2911 - 011
- Fall 2021
- Lab 6 - HTTP Server
- Names:
  - Ben Fouch
  - Nathan Cernik
  - Aidan Regan

An HTTP server

Introduction: (Describe the lab in your own words)




Summary: (Summarize your experience with the lab, what you learned, what you liked,what you disliked, and any suggestions you have for improvement)





"""

import socket
import re
import threading
import os
import mimetypes
import datetime


def main():
    """ Start the server """
    http_server_setup(8080)


def http_server_setup(port):
    """
    Start the HTTP server
    - Open the listening socket
    - Accept connections and spawn processes to handle requests

    :param port: listening port number
    """

    num_connections = 10
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_address = ('', port)
    server_socket.bind(listen_address)
    server_socket.listen(num_connections)
    try:
        while True:
            request_socket, request_address = server_socket.accept()
            print('connection from {0} {1}'.format(request_address[0], request_address[1]))
            # Create a new thread, and set up the handle_request method and its argument (in a tuple)
            request_handler = threading.Thread(target=handle_request, args=(request_socket,))
            # Start the request handler thread.
            request_handler.start()
            # Just for information, display the running threads (including this main one)
            print('threads: ', threading.enumerate())
    # Set up so a Ctrl-C should terminate the server; this may have some problems on Windows
    except KeyboardInterrupt:
        print("HTTP server exiting . . .")
        print('threads: ', threading.enumerate())
        server_socket.close()


def handle_request(request_socket):
    """
    Handle a single HTTP request, running on a newly started thread.

    Closes request socket after sending response.

    Should include a response header indicating NO persistent connection

    :param request_socket: socket representing TCP connection from the HTTP client_socket
    :return: None
    """

    request_line = get_first_line(request_socket)
    (request_type, requested_resource, version, is_valid) = read_request(request_line)

    dictionary = make_dictionary(request_type, requested_resource, version, is_valid)

    send_response(dictionary, request_socket)


# ** Do not modify code below this line.  You should add additional helper methods above this line.

# Utility functions
# You may use these functions to simplify your code.


def send_response(dictionary, tcp_socket):
    """
    Sends a response to a tcp request given a dictionary containing the headers and body and sending socket

    :author:
        - Ben Fouch
        - Nathan Cernik
        - Aidan Regan

    :param dictionary: dictionary containing the headers and the body of the response message
    :param tcp_socket: socket message is being sent from
    :return: void
    """
    space = b' '
    crlf = b'\r\n'
    response = dictionary["version"] + space + dictionary["code"] + space + dictionary["message"] + crlf \
               + b'Date: ' + dictionary["date"] + crlf \
               + b'Content-Length: ' + dictionary["length"] + crlf \
               + b'Content-Type: ' + dictionary["content type"] + crlf \
               + b'Connection: ' + dictionary["connection"] + crlf \
               + crlf \
               + dictionary["body"]

    tcp_socket.sendAll(response)


def make_dictionary(request_type, requested_resource, version, is_valid):
    """
    Makes a dictionary for a response message based off of the request message

    :author:
        - Ben Fouch
        - Nathan Cernik
        - Aidan Regan

    :param request_type: type of network request ("GET, POST, etc.")
    :param requested_resource: name of the resource that was requested
    :param version: HTTP version used in the request
    :param is_valid: true if request is in valid format, false otherwise
    :return: dictionary with response header data and body
    :rtype: dict
    """
    status_code = b'404'
    message = b'Not Found'

    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    connection = b'close'

    if is_valid:
        if (requested_resource == b'index.html' or requested_resource == b'msoe.png' or
                requested_resource == b'style.css' or requested_resource == b'/'):
            status_code = b'200'
            message = b'OK'

        path = ".\\resources\\" + requested_resource.decode("ASCII")
        length = get_file_size(path)
        context_type = get_mime_type(path)

        body = get_body(path, length)

    else:
        status_code = b'400'
        message = b'Bad Request'

    dictionary = {
        "date": date,
        "connection": connection,
        "content type": context_type,
        "length": length,
        "code": status_code,
        "message": message,
        "version": version,
        "body": body
    }

    return dictionary


def get_body(path, length):
    """
    Reads the requested resource, putting it's data into a byte string

    :author:
        - Ben Fouch
        - Nathan Cernik
        - Aidan Regan

    :param path: path of the requested resource
    :param length: length in bytes of the requested resource
    :return: body
    :rtype: bytes
    """
    file = open(path, "r+")
    body = file.read(length)
    file.close()
    return body


def get_first_line(request_socket):
    """
    Parses the first line of the message so it can be broken down

    :author:
        - Ben Fouch
        - Nathan Cernik
        - Aidan Regan

    :param request_socket: socket the request is received at
    :return: the request line
    :rtype: bytes
    """
    line = b''
    while not line.endswith(b'\r\n'):
        line += request_socket.recv(1)
    return line


def read_request(request):
    """
    Reads the request line and returns the important data

    :author:
        - Ben Fouch
        - Nathan Cernik
        - Aidan Regan

    :param request: first line in the request (ex. "GET /index.html HTTP/1.1")
    :return:
        - request_type: type of request (ex. "GET")
        - requested_resource: what resource was requested (ex. "/index.html")
        - version: version of HTTP used (ex. "HTTP/1.1")
        - is_valid: if the HTTP request was valid
    :rtype: tuple
    """
    request_type = ""
    requested_resource = ""
    version = ""
    is_valid = True

    try:
        split_request = request.split(b'\x20')

        request_type = split_request[0]
        requested_resource = split_request[1]
        version = split_request[2]
        if not version == b'HTTP/1.1':
            raise Exception
    except Exception:
        is_valid = False

    return request_type, requested_resource, version, is_valid


def get_mime_type(file_path):
    """
    Try to guess the MIME type of a file (resource), given its path (primarily its file extension)

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If successful in guessing the MIME type, a string representing the content type, such as 'text/html'
             Otherwise, None
    :rtype: int or None
    """

    mime_type_and_encoding = mimetypes.guess_type(file_path)
    mime_type = mime_type_and_encoding[0]
    return mime_type


def get_file_size(file_path):
    """
    Try to get the size of a file (resource) as number of bytes, given its path

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If file_path designates a normal file, an integer value representing the the file size in bytes
             Otherwise (no such file, or path is not a file), None
    :rtype: int or None
    """

    # Initially, assume file does not exist
    file_size = None
    if os.path.isfile(file_path):
        file_size = os.stat(file_path).st_size
    return file_size


main()

# Replace this line with your comments on the lab
