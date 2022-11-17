from IPython.display import HTML, display

def display_refresh_button():
    display(HTML(
        '''
            <script>
                function restart_run_all(outp){
                    // get cell element
                    var cell_element = outp.offsetParent.offsetParent;
                    // which number cell is it?
                    var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
                    console.log(cell_idx)
                    IPython.notebook.kernel.restart();
                    setTimeout(function(){
                        IPython.notebook.execute_cells([cell_idx]);
                    }, 4000)
                }
            </script>
            <style>
            .button{
                border: 1px solid #333333;
                color: #FFFFFF ;
                border-radius: 3px;
                background-color: #2196F3;
                font-family: monospace;
                opacity: .8;
            }
            .button:hover {
                opacity: 1;
                border: 1px solid #2196F3;
                color: #FFFFFF;
                transition: opacity .1s ease-in-out;
                -moz-transition: opacity .1s ease-in-out;
                -webkit-transition: opacity .1s ease-in-out;
                box-shadow: 0 2px 2px -2px rgba(0, 0, 0, .2);
            }
            </style>
            <button class="button" onclick="restart_run_all(this.parentNode.parentNode)">Click to Refresh</button>
        '''
    ))