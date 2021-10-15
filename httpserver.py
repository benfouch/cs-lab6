"""
- CS2911 - 011
- Fall 2021
- Lab 6
- Names:
  - Ben Fouch
  - Nathan Cernik
  - Aidan Regan

An HTTP server

Introduction: (Describe the lab in your own words) :
    This lab is to teach us HTTP responses are structured. It also helps enforce the Http request format.
    This was also effective at teaching us python tools like dictionaries.

Summary: (Summarize your experience with the lab, what you learned, what you liked,what you disliked, and any suggestions you have for improvement)
    This was a great lab! We enjoyed it being a good puzzle and being a bit confusing at type with all type conversions
    Overall, nothing we would change, the supplied methods were very helpful and it was a good lab load for a midterm week.
"""

import socket
import threading
import os
import mimetypes
import datetime
import os.path
from os import path


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
    request_dictionary = make_request_dictionary(request_socket)
    (request_type, requested_resource, version, is_valid) = read_request(request_line)
    dictionary = make_dictionary(request_type, requested_resource, version, is_valid)
    send_response(dictionary, request_socket)
    print(request_dictionary)


def send_response(dictionary, socket):
    """
    Makes and sends the response
    :Author: Nathan Cernik
    """

    space = b' '
    crlf = b'\r\n'
    response = dictionary["version"] + space + dictionary["code"] + space + dictionary["message"] + crlf + \
               b'Date: ' + dictionary["date"] + crlf + \
               b'Content-Length: ' + dictionary["length"] + crlf + \
               b'Content-Type: ' + dictionary["content type"].encode() + crlf + \
               b'Connection: ' + dictionary["connection"] + crlf + crlf + dictionary["body"] + crlf

    socket.send(response)


def make_dictionary(requested_resource, version, is_valid):
    """
    Detriments the values of all the key value pairs for the response message
    :author: All
    """
    status_code = b'404'
    message = b'Not Found'
    length = b''
    context_type = ""
    body = b''
    connection = b'Close'
    date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT').encode()

    if is_valid:
        file_path = ".\\resources\\" + (
            requested_resource.decode("ASCII") if not requested_resource == b'/' else "index.html")

        if path.exists(file_path):
            status_code = b'200'
            message = b'OK'

        if status_code == b'200':
            length = str(get_file_size(file_path)).encode("ASCII")
            context_type = get_mime_type(file_path)
            body = get_body(file_path, int(length.decode("ASCII")))

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


def get_body(file_path, length):
    """
    Gets the bytes object of the body of the request message
    :Author: Ben Fouch
    """
    file = open(file_path, "rb+")
    body = file.read(length)
    file.close()
    return body


def make_request_dictionary(request_socket):
    """
    Makes the dictionary from the key value pairs fo the http request
    :Author: Ben Fouch
    """
    line = b''
    dictionary = {}

    while not line == b'\r\n':
        line = b''
        while not line.endswith(b'\r\n'):
            line += request_socket.recv(1)
        if not line == b'\r\n':
            split_line = line.split(b':')
            dictionary.update({split_line[0]: split_line[1]})

    return dictionary


def get_first_line(request_socket):
    """
    Parses the first line of the message so that we can read it
    :Author: Ben Fouch
    """
    line = b''
    while not line.endswith(b'\r\n'):
        line += request_socket.recv(1)
    return line


def read_request(request):
    """
    Reads the first line of the request, pareses out the values from the request

    :return: The parsed values of the request line
    :Author: Aidan Regan
    """
    request_type = ""
    requested_resource = ""
    version = ""
    is_valid = True

    try:
        split_request = request.split(b'\x20')

        request_type = split_request[0]
        requested_resource = split_request[1]
        version = split_request[2].split(b'\r\n')[0]
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
