"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Upload,
  FileText,
  Code,
  Download,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Search,
} from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type {
  City,
  DataSource,
  ImportDataType,
  ImportPreviewResponse,
  ImportResultResponse,
} from "@/types";
import Link from "next/link";

const dataTypeLabels: Record<ImportDataType, string> = {
  job: "招聘信息",
  rent: "租房信息",
  forum: "论坛帖子",
};

export default function ManualImportPage() {
  const [dataType, setDataType] = useState<ImportDataType>("job");
  const [cityId, setCityId] = useState<string>("");
  const [dataSourceId, setDataSourceId] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [jsonData, setJsonData] = useState<string>("");
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [importResult, setImportResult] = useState<ImportResultResponse | null>(
    null
  );

  const { data: cities } = useQuery({
    queryKey: ["cities", { enabled: true }],
    queryFn: () => api.cities.list({ enabled: true }),
  });

  const { data: sources } = useQuery({
    queryKey: ["sources", { enabled: true }],
    queryFn: () => api.sources.list({ enabled: true }),
  });

  const previewMutation = useMutation({
    mutationFn: async () => {
      if (!file || !cityId || !dataSourceId) {
        throw new Error("请选择文件、城市和数据源");
      }
      return api.import.preview(
        file,
        dataType,
        parseInt(cityId),
        parseInt(dataSourceId)
      );
    },
    onSuccess: (data) => {
      setPreview(data);
      setImportResult(null);
      if (data.invalid_rows > 0) {
        toast.warning(`发现 ${data.invalid_rows} 行数据有问题`);
      } else {
        toast.success(`${data.valid_rows} 行数据验证通过`);
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!file || !cityId || !dataSourceId) {
        throw new Error("请选择文件、城市和数据源");
      }
      return api.import.execute(
        file,
        dataType,
        parseInt(cityId),
        parseInt(dataSourceId)
      );
    },
    onSuccess: (data) => {
      setImportResult(data);
      setPreview(null);
      if (data.success) {
        toast.success(`成功导入 ${data.imported_count} 条数据`);
        setFile(null);
      } else {
        toast.error("导入失败");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const jsonImportMutation = useMutation({
    mutationFn: async () => {
      if (!jsonData || !cityId || !dataSourceId) {
        throw new Error("请填写JSON数据、选择城市和数据源");
      }
      let rows;
      try {
        rows = JSON.parse(jsonData);
        if (!Array.isArray(rows)) {
          throw new Error("JSON数据必须是数组格式");
        }
      } catch (e) {
        throw new Error("JSON格式错误: " + (e as Error).message);
      }
      return api.import.importJson({
        data_type: dataType,
        city_id: parseInt(cityId),
        data_source_id: parseInt(dataSourceId),
        rows,
      });
    },
    onSuccess: (data) => {
      setImportResult(data);
      if (data.success) {
        toast.success(`成功导入 ${data.imported_count} 条数据`);
        setJsonData("");
      } else {
        toast.error("导入失败");
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(null);
      setImportResult(null);
    }
  };

  const handleDownloadTemplate = () => {
    window.open(api.import.getTemplateUrl(dataType), "_blank");
  };

  const isFormValid = cityId && dataSourceId;

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">数据导入</h1>
            <p className="text-sm text-muted-foreground">手动导入数据到系统</p>
          </div>
          <Button variant="outline" asChild>
            <Link href="/manual-import/guide">
              <Search className="h-4 w-4 mr-2" />
              搜索指南
            </Link>
          </Button>
        </div>

        {/* Configuration Card */}
        <Card>
          <CardHeader>
            <CardTitle>导入配置</CardTitle>
            <CardDescription>选择数据类型、城市和数据源</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>数据类型</Label>
                <Select
                  value={dataType}
                  onValueChange={(v) => setDataType(v as ImportDataType)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(dataTypeLabels).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>城市</Label>
                <Select value={cityId} onValueChange={setCityId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择城市" />
                  </SelectTrigger>
                  <SelectContent>
                    {cities?.map((city) => (
                      <SelectItem key={city.id} value={String(city.id)}>
                        {city.name} ({city.province})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>数据源</Label>
                <Select value={dataSourceId} onValueChange={setDataSourceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择数据源" />
                  </SelectTrigger>
                  <SelectContent>
                    {sources?.map((source) => (
                      <SelectItem key={source.id} value={String(source.id)}>
                        {source.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadTemplate}
              >
                <Download className="h-4 w-4 mr-2" />
                下载{dataTypeLabels[dataType]}模板
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Import Methods */}
        <Tabs defaultValue="file">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="file" className="gap-2">
              <Upload className="h-4 w-4" />
              文件上传
            </TabsTrigger>
            <TabsTrigger value="json" className="gap-2">
              <Code className="h-4 w-4" />
              JSON导入
            </TabsTrigger>
          </TabsList>

          <TabsContent value="file">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  文件上传
                </CardTitle>
                <CardDescription>
                  支持 CSV 和 Excel 格式（.csv, .xlsx, .xls）
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="file">选择文件</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileChange}
                  />
                  {file && (
                    <p className="text-sm text-muted-foreground">
                      已选择: {file.name} (
                      {(file.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => previewMutation.mutate()}
                    disabled={!file || !isFormValid || previewMutation.isPending}
                  >
                    {previewMutation.isPending && (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    )}
                    预览数据
                  </Button>
                  <Button
                    variant="default"
                    onClick={() => executeMutation.mutate()}
                    disabled={
                      !file || !isFormValid || executeMutation.isPending
                    }
                  >
                    {executeMutation.isPending && (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    )}
                    执行导入
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="json">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  JSON导入
                </CardTitle>
                <CardDescription>
                  直接粘贴JSON格式的数据数组
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="json">JSON数据</Label>
                  <Textarea
                    id="json"
                    placeholder={`[
  {
    "title": "Python开发工程师",
    "company": "某科技公司",
    "salary_min": 15000,
    "salary_max": 25000,
    ...
  }
]`}
                    className="font-mono h-48"
                    value={jsonData}
                    onChange={(e) => setJsonData(e.target.value)}
                  />
                </div>

                <Button
                  onClick={() => jsonImportMutation.mutate()}
                  disabled={
                    !jsonData || !isFormValid || jsonImportMutation.isPending
                  }
                >
                  {jsonImportMutation.isPending && (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  )}
                  导入JSON数据
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Preview Results */}
        {preview && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                数据预览
              </CardTitle>
              <CardDescription>
                共 {preview.total_rows} 行，
                <span className="text-green-600">
                  {preview.valid_rows} 行有效
                </span>
                ，
                <span className="text-red-600">
                  {preview.invalid_rows} 行无效
                </span>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {preview.errors.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="font-medium text-red-800 flex items-center gap-2 mb-2">
                    <AlertCircle className="h-4 w-4" />
                    验证错误
                  </h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    {preview.errors.map((err, i) => (
                      <li key={i}>
                        第 {err.row} 行, 字段 {err.field}: {err.error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {preview.preview.length > 0 && (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(preview.preview[0]).map((key) => (
                          <TableHead key={key}>{key}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {preview.preview.map((row, i) => (
                        <TableRow key={i}>
                          {Object.values(row).map((val, j) => (
                            <TableCell key={j} className="max-w-xs truncate">
                              {val !== null && val !== undefined
                                ? String(val)
                                : "-"}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Import Results */}
        {importResult && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {importResult.success ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-600" />
                )}
                导入结果
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <Badge
                  variant="outline"
                  className="bg-green-50 text-green-700 border-green-200"
                >
                  成功导入: {importResult.imported_count}
                </Badge>
                <Badge
                  variant="outline"
                  className="bg-yellow-50 text-yellow-700 border-yellow-200"
                >
                  跳过: {importResult.skipped_count}
                </Badge>
              </div>

              {importResult.errors.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h4 className="font-medium text-red-800 flex items-center gap-2 mb-2">
                    <AlertCircle className="h-4 w-4" />
                    导入错误
                  </h4>
                  <ul className="text-sm text-red-700 space-y-1">
                    {importResult.errors.map((err, i) => (
                      <li key={i}>
                        第 {err.row} 行: {err.error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
