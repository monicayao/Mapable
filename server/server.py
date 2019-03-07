import http.server
import socketserver
import json
import queue
import pprint
import copy
import os

PORT = int(os.environ.get("PORT", "8000"))
pp = pprint.PrettyPrinter()

# The path algorithm
def pathAlg(jsonObj):
    startNode = jsonObj["startLocation"]
    endNode = jsonObj["endLocation"]
    startHourStr = jsonObj["startTime"]
    totalTime = jsonObj["totalTime"]
    waitTimes = jsonObj["listOfLocations"]

    distanceMatrix = {}
    for source, dest, distance in jsonObj["distanceInfo"]:
        if source not in distanceMatrix:
            distanceMatrix[source] = {}
        distanceMatrix[source][dest] = distance

        source, dest = dest, source
        if source not in distanceMatrix:
            distanceMatrix[source] = {}
        distanceMatrix[source][dest] = distance

    # pp.pprint(distanceMatrix)
    nodes = list(waitTimes.keys())
    paths = uniformCostSearch(startNode, endNode, waitTimes, totalTime, distanceMatrix, 10)

    pp.pprint(paths)

    paths = [path for cost, path in list(reversed(paths))]

    return paths


# returns lists of lists of paths from root
def uniformCostSearch(startLoc, endLoc, waitTimes, maxTime, distanceMatrix, numPaths):
    visited = set()

    priorityQueue = queue.PriorityQueue()
    goodPaths = queue.PriorityQueue(numPaths)

    # objects of form
    # (cost, ("nameOfLocation", [visited1, visited2]))
    # PriorityQueue takes in objects of form (cost, object), min cost first

    priorityQueue.put_nowait((0, (startLoc, [startLoc])))

    while not priorityQueue.empty():
        timeTaken, (location, path) = priorityQueue.get_nowait()
        # print(path)

        savedPath = tuple(sorted(path))
        if savedPath in visited:
            continue

        visited.add(savedPath)

        if (timeTaken > maxTime):
            return unwrapPriorityQueue(goodPaths)

        # guaranteed to visit least cost first
        if (location == endLoc):
            # get rid worst path
            if (goodPaths.full()):
                goodPaths.get_nowait()
            goodPaths.put_nowait((timeTaken, path))
            continue

        # we want to look at each child, so long as it has not been visited
        for nextLocation, timeToLoc in distanceMatrix[location].items():
            if nextLocation in path:
                continue

            # update path with the location we're at now
            newPath = copy.deepcopy(path)
            newPath.append(nextLocation)

            totalTime = timeTaken + waitTimes[location] + timeToLoc

            priorityQueue.put_nowait((totalTime, (nextLocation, newPath)))

    return unwrapPriorityQueue(goodPaths)

def unwrapPriorityQueue(goodPaths):
    paths = []
    while not goodPaths.empty():
        paths.append(goodPaths.get_nowait())
    return paths

class HTTPHandler(http.server.BaseHTTPRequestHandler):

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        http.server.BaseHTTPRequestHandler.end_headers(self)

    # every HTTP response needs a header
    def _set_headers(self, type):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type',type)
        self.end_headers()

    def do_GET(self):
        print("received GET")

        self._set_headers('text/html')

        indexPath = os.path.join('..', 'client', 'index.html')
        indexFile = open(indexPath)

        self.wfile.write(indexFile.read().encode())
        indexFile.close()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        print("received POST")
        self._set_headers('application/json')

        content_len = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_len).decode('utf-8')
        input_obj = json.loads(post_body)
        print(input_obj)

        result = pathAlg(input_obj)

        response = result
        self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    if dirname != '':
        os.chdir(dirname)

    with socketserver.TCPServer(("", PORT), HTTPHandler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
