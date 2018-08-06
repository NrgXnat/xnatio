import ipywidgets as widgets
from dateutil import parser as dateParser


class Data:
    def __init__(self, data, options=None):
        """
            Initializes the object

            Parameters
            ----------
            data: list or dict
                the data to be processed and aggregated
            options:  dict
                a dict of options

                "keys": list
                    a list of strings used to determine which properties of objects in arrays can be used to determine a key for that object
                    default: ["field", "names"]

                "parse": list [str]
                    what types should be automatically parsed
                    default: ["int", "float", "date"]

            Returns
            -------
            Data
                The Data object
        """
        self.data = data
        self.paths = {}
        self.formattedData = None
        self.columns = {}  # name:rule
        defaults = {
            "keys": ["field", "names"],
            "parse": ["int", "float", "date"]
        }
        if isinstance(options, dict):
            defaults.update(options)

        self.options = defaults

    @staticmethod
    def path2str(path):
        """
            Makes a string from a path

            Parameters
            ----------
            path: list
                the path to be converted

            Returns
            -------
            str
                the string representing the path
        """
        string = ""

        for loc in path:
            if isinstance(loc, str):
                string += "/" + loc

        return string

    def select_path(self, path):
        """
            Selects a path

            Parameters
            ----------
            path: list
                the new path to be added

            Returns
            -------
            dict
                the dict containing all selected paths
        """

        self.formattedData = None
        pathPretty = Data.path2str(path)
        print(pathPretty)
        self.paths[pathPretty] = path
        return self.paths

    def data_ui(self):
        """
            Returns a gui to allow the user to select data fields

            Returns
            -------
            ipywidget
                an ipywidget to be displayed
        """
        pathContainer = widgets.VBox()

        fullPathContainer = widgets.VBox()

        addButton = widgets.Button(description="Add")
        removeButton = widgets.Button(description="Remove")

        fullPathContainer.children = [pathContainer, addButton, removeButton]

        def getIndices(obj):
            def childrenToIndices(children):
                childrenDict = {}
                for index, child in enumerate(children):
                    childId = ""
                    try:
                        childId = "" + child["field"]
                    except:
                        try:
                            childId = "" + child["data_fields"]["name"]
                        except:
                            raise Error("children cannot be converted to dict")
                    childrenDict[childId] = [childId]

                return childrenDict

            def formatIfFinal(obj, index):
                try:
                    item = obj[index]
                except:
                    return index
                else:
                    if isinstance(item, list) or isinstance(item, dict):
                        return index + "/"
                    else:
                        return index

            indices = {}
            if isinstance(obj, dict):
                for index, value in obj.items():
                    # it's a dict
                    if isinstance(value, list):
                        try:
                            childrenIndices = childrenToIndices(value)
                        except:
                            indices[formatIfFinal(obj, index)] = [index]
                        else:
                            for childId, childIndex in childrenIndices.items():
                                indices[childId + "/"] = [index] + childIndex
                    else:
                        indices[formatIfFinal(obj, index)] = [index]

                return indices
            elif isinstance(obj, list):
                for count, child in enumerate(obj):
                    childIndices = getIndices(child)
                    for childFakeIndex, childIndex in childIndices.items():
                        try:
                            # sees if the index already exists
                            x = indices[childFakeIndex]
                        except:
                            indices[childFakeIndex] = [count - len(obj)] + childIndex
                return indices
            else:
                raise Exception("no more indices")

        def addPathWidget(b=None):
            def dataFromIndices(data, indices):
                #     print(indices)
                try:
                    currIndex = indices[0]
                except:
                    return [data]
                else:
                    if isinstance(data, list):
                        if isinstance(currIndex, int) and currIndex < 0:
                            out = []
                            for item in data:
                                try:
                                    out += dataFromIndices(item, indices[1:len(indices)])
                                except:
                                    pass
                            return out
                        elif isinstance(currIndex, str):
                            for item in data:
                                try:
                                    if item['field'] == currIndex:
                                        return dataFromIndices(item, indices[1:len(indices)])
                                except:
                                    try:
                                        if item['data_fields']['name'] == currIndex:
                                            return dataFromIndices(item, indices[1:len(indices)])
                                    except:
                                        pass
                    else:
                        try:
                            return dataFromIndices(data[currIndex], indices[1:len(indices)])
                        except:
                            pass
                    raise Exception("Index " + currIndex + " is invalid")

            path = []
            for i in range(len(pathContainer.children)):
                index = pathContainer.children[i].value
                p = index[1:len(index)]
                path += p
            try:
                data = dataFromIndices(self.data, path)
                indices = getIndices(data)
            except:
                # it's final, add the path to something
                self.select_path(path)
            else:
                try:
                    pathContainer.children[-1].disabled = True
                except:
                    pass
                finally:
                    for key, value in indices.items():
                        indices[key][0] = key
                    newDD = widgets.Dropdown(options=indices, disabled=False)
                    try:
                        newDD.value = indices['experiments/']
                    except:
                        pass
                    c = pathContainer.children
                    c += (newDD,)
                    pathContainer.children = c

        def removePathWidget(b=None):
            if (len(pathContainer.children) > 1):
                c = pathContainer.children
                c = c[0:-1]
                pathContainer.children = c
                pathContainer.children[-1].disabled = False

        addButton.on_click(addPathWidget)
        removeButton.on_click(removePathWidget)

        addPathWidget()

        return fullPathContainer

    #     def get_data_better(self, prettyPath, options=None):
    #         """
    #             Does get_data except with the pretty path itself, which should be more robust

    #             Parameters
    #             ----------

    #             prettyPath: dict
    #                 the path

    #             options: dict
    #                 just look at the other docs for this
    #         """

    def get_data(self, options=None):
        """
           Aggregates and returns data

           Flattens out the heirarchal data by combining like data into points using their least common ancestor

           Parameters
           ----------
           options: dict
               Options for the aggregation

               "format": "lists" | "points"
                   the format of the data to be returned
                   list returns a dict of labelled lists of data
                   points returns a list of labelled dict data points
                   default: "points"

            Returns
            -------
            list or dict
                (see options > "format")
        """

        def combinePaths(paths):
            #     print(paths)
            if (len(paths) == 1 and len(paths[0]) == 0):
                return None
            possibleIndices = {}
            for path in paths:
                currIndex = path[0]
                try:
                    if int(currIndex) < 0:
                        currIndex = -1
                except:
                    pass
                finally:
                    try:
                        possibleIndices[currIndex].append(path[1:len(path)])
                    except:
                        possibleIndices[currIndex] = [path[1:len(path)]]
            if len(possibleIndices) == 1:
                for key, value in possibleIndices.items():
                    return {key: combinePaths(value)}
            else:
                pathsDict = {}
                for key, value in possibleIndices.items():
                    pathsDict[key] = combinePaths(value)
                return pathsDict

        def getDataPointsHelper(data, combinedPaths, name=""):

            def parse(val):
                # only parse strings
                if isinstance(val, str):
                    try:
                        if "int" in self.options["parse"]:
                            return int(val)
                        else:
                            raise Exception()
                    except:
                        try:
                            if "float" in self.options["parse"]:
                                return float(val)
                            else:
                                raise Exception()
                        except:
                            try:
                                if "date" in self.options["parse"]:
                                    return dateParser.parse(val)
                                else:
                                    raise Exception()
                            except:
                                #                             traceback.print_exc()
                                return val
                else:
                    return val

            returnArray = []
            for key, values in combinedPaths.items():
                if isinstance(data, list):
                    try:
                        if (int(key) >= 0):
                            # somewhat sketchy code here basically is basically just forcing the except to run
                            raise Exception()
                        try:
                            for d in data:
                                try:
                                    returnArray += getDataPointsHelper(d, values, name)
                                except:
                                    pass
                            # if were here, theres only one index, so just return it
                            return returnArray
                        #                             print(len(returnArray))
                        except:
                            pass
                    except:
                        # if at this point, it should be a string index
                        for item in data:
                            try:
                                if item['field'] == key:
                                    returnArray += getDataPointsHelper(item, values, name + "/" + key)
                                else:
                                    raise Exception()
                            except:
                                try:
                                    if item['data_fields']['name'] == key:
                                        returnArray += getDataPointsHelper(item, values, name + "/" + key)
                                    else:
                                        raise Exception()
                                except:
                                    pass

                elif isinstance(data, dict):
                    try:
                        if values == None:
                            returnArray += [{name + "/" + key: parse(data[key])}]
                        else:
                            try:
                                #                                 print(str(key) + " " + str(values))
                                returnArray += getDataPointsHelper(data[key], values, name + "/" + key)
                            except:
                                #                                 returnArray.append(dataDataPointsHelper)
                                #                                 returnArray.append({key: None})
                                pass
                    except:
                        #                         traceback.print_exc()
                        returnArray.append({name + "/" + key: None})

            return combineData(returnArray)

        def combineData(data):
            for i in range(len(data)):
                if data[i] == None:
                    data[i] = {"None": None}
                if not isinstance(data[i], list):
                    #             print("in")
                    data[i] = [data[i]]
            #     print("data:")
            #             print(data)
            return cartesianProductMany(data)

        def cartesianProductMany(sets):
            a = sets[0]
            for i in range(1, len(sets)):
                a = cartesianProduct(a, sets[i])
            return a

        def cartesianProduct(a, b):
            #     print(a)
            #     print(b)
            points = []
            for i in a:
                for j in b:
                    c = {}
                    c.update(i)
                    c.update(j)
                    points.append(c)
            return points

        defaults = {
            "format": "points"
        }
        if isinstance(options, dict):
            for key, value in options.items():
                defaults[key] = value

        if not self.formattedData == None:
            if defaults["format"] == "list" or defaults["format"] == "lists":
                if isinstance(self.formattedData, dict):
                    return self.formattedData
            else:  # format is the default, points
                if isinstance(self.formattedData, list):
                    return self.formattedData

        pathsArray = []
        for key, path in self.paths.items():
            pathsArray.append(path)

        combinedPaths = combinePaths(pathsArray)

        dataPoints = getDataPointsHelper(self.data, combinedPaths)

        for index, point in enumerate(dataPoints):
            # keeps going until it 'stabilizes', since a column may require another
            numFailed = 0

            while True:
                oldNumFailed = numFailed
                numFailed = 0
                for name, rule in self.columns.items():
                    if not name in dataPoints[index]:
                        try:
                            dataPoints[index][name] = eval(rule)
                        except:
                            numFailed += 1

                if oldNumFailed == numFailed:
                    break

        if defaults["format"] == "list":
            dataArrays = {}
            # first, get all the
            for point in dataPoints:
                for name, value in point.items():
                    if not value == None:
                        dataArrays[name] = []

            for point in dataPoints:
                try:
                    for name, _ in dataArrays.items():
                        if point[name] == None:
                            raise Exception()

                    for name, _ in dataArrays.items():
                        dataArrays[name].append(point[name])
                except:
                    pass
            self.formattedData = dataArrays
        else:
            self.formattedData = dataPoints

        return self.formattedData

    def set_option(self, key, value):
        """
            Sets an option

            Parameters
            ----------
            key: string
                the key (or name) of the object to be set

            value: Any
                the value to be attributed to the key

            Return
            ------
            None
        """
        self.options[key] = value

    def set_options(self, options):
        """
            Sets multiple options

            A function to set multiple options

            Parameters
            ----------
            options: dict
                a dict of options in form "key":"value" to be set
        """

        if isinstance(options, dict):
            self.options.update(options)

    # this method is vulnerable to attacks, but it should be al
    def add_column(self, name, exp, subs):
        """
            Adds a new calculated column

            Parameters
            ----------
            exp: str
                the expression to caluate the column
                note: variables to be substituted must be wrapped in backticks (`)

            subs: dict
                substitutions to be made in the expression
                ex: {"x":"experiment/dian:cdrsuppdata/data_feilds/date"}

            Returns
            -------
            columns: dict
        """

        rule = exp

        for var, sub in subs.items():
            # add backticks
            if var[0] != '`':
                var = '`' + var

            if var[-1] != '`':
                var = var + '`'

            # this code is a little sketchy

            rule = rule.replace(var, 'point["' + sub + '"]')

        self.columns[name] = rule

        self.formattedData = None

        return self.columns

    # todo:: UI for adding columns
    def add_column_ui(self):
        """
            Returns the UI for defining new calculated columns

            Returns
            -------
            widgets.VBox
        """
        container = widgets.VBox()
        subsContainer = widgets.VBox()
        colsContainer = widgets.VBox()
        expContainer = widgets.HBox()
        addColButton = widgets.Button(description="Add Column")
        addSubButton = widgets.Button(description="Add Variable")

        def add_sub(e=None):
            sub = widgets.HBox()
            nameField = widgets.Text(placeholder="name")
            options = []

            for name, _ in self.paths.items():
                options.append(name)

            for name, _ in self.columns.items():
                options.append(name)

            dd = widgets.Dropdown(options = options, title = " = ")

            sub.children = (nameField, dd)

            c = subsContainer.children
            c += (sub,)
            subsContainer.children = c

        def setup():
            # setup expContainer
            expContainer.children = (
                widgets.Text(placeholder="Column Name"),
                widgets.Text(placeholder="Expression")
            )

            # setup colsContainer
            cols = []

            for name, rule in self.columns.items():
                cols.append(widgets.HTML(value=name + " = " + rule))

            colsContainer.children = cols

            # setup subsContainer
            subsContainer.children = []
            add_sub()

            # setup container
            container.children = (
                widgets.HTML(value="Define variables below that will be substituted into the expression."),
                subsContainer,
                addSubButton,
                widgets.HTML(value="Enter the name of the new column and the expression that defines it. Variables defined above must be escaped with backticks (`)."),
                expContainer,
                addColButton,
                colsContainer
            )

        def add_col(e=None):
            name = expContainer.children[0].value
            exp = expContainer.children[1].value

            subs = {}


            for sub in subsContainer.children:
                var = sub.children[0].value

                print(var)
                val = sub.children[1].value

                subs[var] = val

            self.add_column(name, exp, subs)

            setup()

        setup()

        addColButton.on_click(add_col)
        addSubButton.on_click(add_sub)

        return container
