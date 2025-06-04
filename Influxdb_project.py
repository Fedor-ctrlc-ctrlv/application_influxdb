import tkinter as tk
from tkinter import messagebox, filedialog
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
from influxdb_client.client.query_api import QueryApi

class InfluxDBWriterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Запись данных в InfluxDB")
        self.root.geometry("400x300")
        
        
        self.url = "http://localhost:8086"
        self.token = "название вашего токена"
        self.org = "название организации"
        self.bucket = "название вашей бд"
    
        self.create_widgets()
        
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
    
    def create_widgets(self):
        tk.Label(self.root, text="Название трубы:").pack(pady=5)
        self.pipe_name_entry = tk.Entry(self.root, width=40)
        self.pipe_name_entry.pack(pady=5)
        
        tk.Label(self.root, text="Температура (°C):").pack(pady=5)
        self.temp_entry = tk.Entry(self.root, width=40)
        self.temp_entry.pack(pady=5)
        
        tk.Label(self.root, text="Давление (бар):").pack(pady=5)
        self.pressure_entry = tk.Entry(self.root, width=40)
        self.pressure_entry.pack(pady=5)
        
        
        self.write_btn = tk.Button(
            self.root, 
            text="Записать данные", 
            command=self.write_to_influx,
            bg="#4CAF50",
            fg="white",
            height=2,
            width=20
        )
        self.write_btn.pack(pady=20)
        
         # Кнопка экспорта
        self.export_btn = tk.Button(
            self.root,
            text="Экспорт в CSV",
            command=self.export_to_csv,
            bg="#2196F3",
            fg="white",
            height=2,
            width=15
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        

        self.status_var = tk.StringVar()
        self.status_var.set("Готов к записи")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
    
    def write_to_influx(self):
        try:

            pipe_name = self.pipe_name_entry.get()
            temperature = float(self.temp_entry.get())
            pressure = float(self.pressure_entry.get())
            point = Point("pipe_measurements") \
                .tag("pipe_name", pipe_name) \
                .field("temperature", temperature) \
                .field("pressure", pressure) \
                .time(datetime.datetime.utcnow())
            
            
            self.write_api.write(bucket=self.bucket, record=point)
            
            self.pipe_name_entry.delete(0, tk.END)
            self.temp_entry.delete(0, tk.END)
            self.pressure_entry.delete(0, tk.END)
            
            self.status_var.set(f"Данные записаны в {datetime.datetime.now().strftime('%H:%M:%S')}")
            messagebox.showinfo("Успех", "Данные успешно записаны в базу данных!")
            
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числовые значения для температуры и давления")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось записать данные: {str(e)}")
            self.status_var.set("Ошибка записи")
            
    def export_to_csv(self):
        try:
            # Запрос для получения данных из InfluxDB
            query = f'''
            from(bucket: "{self.bucket}")
              |> range(start: -24h)
              |> filter(fn: (r) => r._measurement == "pipe_measurements")
              |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
              |> keep(columns: ["_time", "pipe_name", "temperature", "pressure"])
              |> sort(columns: ["_time"], desc: true)
            '''
            
            
            result = self.query_api.query_data_frame(query)
            
            if result.empty:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
                return
            
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                title="Сохранить данные как"
            )
            
            if file_path:
                
                result = result.rename(columns={
                    '_time': 'Время',
                    'pipe_name': 'Труба',
                    'temperature': 'Температура (°C)',
                    'pressure': 'Давление (бар)'
                })
                
                # Сохраняем в CSV
                result.to_csv(file_path, index=False, encoding='utf-8')
                
                self.status_var.set(f"Данные экспортированы в {file_path}")
                messagebox.showinfo("Успех", "Экспорт завершен успешно!")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")
            self.status_var.set("Ошибка экспорта")

if __name__ == "__main__":
    root = tk.Tk()
    app = InfluxDBWriterApp(root)
    root.mainloop()