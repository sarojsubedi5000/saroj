from flask import Flask, render_template, request, redirect, session
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Home route for login and connection setup
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the user input
        instance = request.form.get('instance')
        username = request.form.get('username')
        password = request.form.get('password')

        try:    
            # Save the connection information in the session
            connection_string = f"DRIVER={{SQL Server}};SERVER={instance};UID={username};PWD={password}"
            connection = pyodbc.connect(connection_string)
            session['connection_string'] = connection_string

            # Store instance, username, and password in session to avoid re-entry
            session['instance'] = instance
            session['username'] = username
            session['password'] = password

            # Fetch the list of databases
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sys.databases")
            databases = [row[0] for row in cursor.fetchall()]
            session['databases'] = databases

            # Set the default database to 'master' if available, else the first one
            if not session.get('database'):
                session['database'] = 'master' if 'master' in databases else (databases[0] if databases else None)

            cursor.close()
            connection.close()

            return redirect('/dashboard')  # Redirect to the dashboard after successful login
        except Exception as e:
            return f"Error connecting to the database: {str(e)}"

    # Check if instance, username, and password are in session
    if 'instance' in session and 'username' in session and 'password' in session:
        # If they exist, use them to prefill the form fields
        instance = session['instance']
        username = session['username']
        password = session['password']
    else:
        instance = username = password = None  # Otherwise, leave them as None (empty)

    return render_template('index.html', instance=instance, username=username, password=password)

# Dashboard route to display databases and handle SQL queries
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        action = request.form.get('action')
        selected_db = session.get('database')
        connection_string = session.get('connection_string')

        if not selected_db or not connection_string:
            return redirect('/')

        try:
            # Connect to the selected database
            connection = pyodbc.connect(connection_string + f";DATABASE={selected_db}")
            cursor = connection.cursor()

            result_message = None
            query_result = None
            headers = None

            if action == "alter_table":
                # SQL ALTER TABLE query to add a new column
                query = "ALTER TABLE userregistration ADD projecttype VARCHAR(255)"
                try:
                    cursor.execute(query)
                    connection.commit()
                    result_message = "User Registration Issue Has Been Solved "
                except Exception as e:
                    result_message = f"Error altering table: {str(e)}"

            elif action == "sales_ird":
                # SQL query to remove duplicate value if found in sales_ird_info table 
                query = """
                WITH cte AS (
                    SELECT 
                        invno,
                        Printvalue,
                        Printdate,
                        printed_by,
                        is_ird_sync,
                        ird_res,
                        ird_resText,
                        is_real_Time,
                        source,
                        transactionId,
                        VatReturnAmount,
                        payerId,
                        ROW_NUMBER() OVER (
                            PARTITION BY 
                                invno,
                                Printvalue,
                                Printdate,
                                printed_by,
                                is_ird_sync,
                                ird_res,
                                ird_resText,
                                is_real_Time,
                                source,
                                transactionId,
                                VatReturnAmount,
                                payerId
                            ORDER BY invno
                        ) AS rank
                    FROM Sales_Ird_Info
                )
                DELETE FROM cte WHERE rank = 2;
                """
                try:
                    cursor.execute(query)  # Try executing the query
                    headers = [desc[0] for desc in cursor.description]  # Get headers if the query executes
                    query_result = cursor.fetchall()  # Get the results
                except Exception as e:
                    result_message = f"Error executing query: {str(e)}"  # If error occurs, catch it and store the message
                else:
                    result_message = "Query executed successfully."  # If no error occurs, confirm success
            
            elif action == "backdate":
                # SQL ALTER TABLE query to add a new column
                query = "alter table lastbackup add Backupdate varchar(255);"
                try:
                    cursor.execute(query)
                    connection.commit()
                    result_message = "Backdate Issue Has Been Sucessfully Resolved"
                except Exception as e:
                    result_message = f"Error Running query: {str(e)}"

            elif action == "stockqty":
                # Update sales details stockqty with qty 
                query = "update sales_details set StockQty=qty where StockQty<>qty;"
                try:
                    cursor.execute(query)
                    connection.commit()
                    result_message = "Stock qty has been sucessfully updated"
                except Exception as e:
                    result_message = f"Error Running query: {str(e)}"
            
            elif action == "Trigger":
                # Update sales details stockqty with qty 
                query = """ 
                    DROP TRIGGER [dbo].[PREVENT_DELETE_Sales_Master]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SALES_MASTER]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SALES_DETAILS]
                    DROP TRIGGER [dbo].[PREVENT_DELETE_SALES_DETAILS]
                    DROP TRIGGER [dbo].[PREVENT_DELETE_SALES_TERM]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SALES_TERM]
                    DROP TRIGGER [dbo].[PREVENT_DELETE_SalesReturn_Master]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SalesReturn_Master]
                    DROP TRIGGER [dbo].[PREVENT_DELETE_SalesReturn_Details]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SalesReturn_Details]
                    DROP TRIGGER [dbo].[PREVENT_DELETE_SalesReturn_Term]
                    DROP TRIGGER [dbo].[PREVENT_UPDATE_SalesReturn_Term]
                """
                try:
                    cursor.execute(query)
                    connection.commit()
                    result_message = "Trigger Has been droped"
                except Exception as e:
                    result_message = f"Error LOL: {str(e)}"
                
            elif action == "Opening":
                # Update sales details stockqty with qty 
                query = "update Consolidate_Opening set Conso_Code=REPLACE(CONSO_CODE,'OB-','');"
                try:
                    cursor.execute(query)
                    connection.commit()
                    result_message = "Opening Issue has been resolved"
                except Exception as e:
                    result_message = f"Error Running query: {str(e)}"

                    








            cursor.close()
            connection.close()

            return render_template(
                'dashboard.html',
                databases=session.get('databases'),
                selected_database=selected_db,
                query_result=query_result,
                headers=headers,
                result_message=result_message
            )

        except Exception as e:
            return f"Error connecting to the database: {str(e)}"

    return render_template(
        'dashboard.html',
        databases=session.get('databases'),
        selected_database=session.get('database')
    )

# Select the database to work with
@app.route('/select_db', methods=['POST'])
def select_db():
    selected_db = request.form.get('database')
    session['database'] = selected_db  # Update the selected database in the session
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
