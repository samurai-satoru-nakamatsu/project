import base64
from io import BytesIO
from matplotlib.figure import Figure
import numpy as np


def google_analytics_graph(analytics):
    print(np.array(analytics['rows']))
    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot(np.array(analytics['rows'])[:,0], np.array(analytics['rows'])[:,1])
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data