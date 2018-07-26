import ipywidgets as widgets

class Data:
    def __init__(self, data, options=None):
        self.data = data
        self.paths = {}
        defaults = {
            keys: ["field", "names"]
        }
        if isinstance(options, dict):
            for key, value in options.items():
                defaults[key] = value
        self.options = defaults

    def get_gui(self):
        pathContainer = widgets.VBox()

        fullPathContainer = widgets.VBox()

        addButton = widgets.Button(description="Add")
        removeButton = widgets.Button(description="Remove")

        fullPathContainer.children = [groupsDisplayContainer, pathContainer, addButton, removeButton]



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
                    childrenDict[childId] = [index]

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
                    if isinstance(currIndex, int) and currIndex < 0:
                        out = []
                        for item in data:
                            try:
                                out += dataFromIndices(item, indices[1:len(indices)])
                            except:
                                pass
                        return out
                    else:
                        try:
                            return dataFromIndices(data[currIndex], indices[1:len(indices)])
                        except:
                            raise Exception("Index " + currIndex + " is invalid")

            path = []
            for i in range(len(pathContainer.children)):
                index = pathContainer.children[i].value
                path += index[1:len(index)]
            try:
                indices = getIndices(dataFromIndices(experimentSamples, path))
            except:
                # it's final, add the path to something
                pathPretty = ""
                for i in range(len(pathContainer.children)):
                    pathPretty += pathContainer.children[i].value[0]
                #         print(pathPretty)
                #         print("[" + "][".join(str(p) for p in path) + "]")
                paths[pathPretty] = path
                return
            else:
                try:
                    pathContainer.children[-1].disabled = True
                except:
                    pass
                finally:
                    for key, value in indices.items():
                        indices[key][0] = key
                    #             print(indices)
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